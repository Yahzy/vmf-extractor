import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import json
import threading
from typing import List, Tuple

from parser_vmf import VMFParser
from extract_mat import MaterialExtractor
from extract_mdl import ModelExtractor
from extract_snd import SoundExtractor

# Try to import tkinterdnd2 for proper drag & drop
try:
	from tkinterdnd2 import DND_FILES, TkinterDnD
	HAS_DND = True
except ImportError:
	HAS_DND = False


class ContentPathManager:
	def __init__(self):
		self.paths: List[Tuple[str, str]] = []
		self.config_file = "paths.json"
		self.load_config()

	def add_path(self, path: str, path_type: str):
		if (path, path_type) not in self.paths:
			self.paths.append((path, path_type))
			self.save_config()

	def remove_path(self, index: int):
		if 0 <= index < len(self.paths):
			del self.paths[index]
			self.save_config()

	def get_paths_by_type(self, path_type: str) -> List[str]:
		return [path for path, ptype in self.paths if ptype == path_type]

	def get_all_content_paths(self) -> List[str]:
		content_paths = []

		for path, path_type in self.paths:
			if path_type == "content":
				content_paths.append(path)
			elif path_type == "addons" and os.path.exists(path):
				content_paths.extend([
					os.path.join(path, addon) for addon in os.listdir(path)
					if os.path.isdir(os.path.join(path, addon))
				])

		return content_paths

	def save_config(self):
		try:
			with open(self.config_file, 'w', encoding='utf-8') as f:
				json.dump(self.paths, f, indent=2, ensure_ascii=False)
		except Exception as e:
			print(f"Save error: {e}")

	def load_config(self):
		if not os.path.exists(self.config_file):
			return
		try:
			with open(self.config_file, 'r', encoding='utf-8') as f:
				self.paths = json.load(f)
		except Exception as e:
			print(f"Load error: {e}")
			self.paths = []


class VMFExtractorGUI:
	def __init__(self, root):
		self.root = root
		self.root.title("VMF Content Extractor")
		self.root.geometry("800x640")

		# Path manager
		self.path_manager = ContentPathManager()

		# Variables
		self.extraction_running = False
		self.selected_vmf = None

		# Create interface
		self.create_widgets()
		self.refresh_paths_list()

		# Configure drag & drop
		self.setup_drag_drop()

	def create_widgets(self):
		# Main frame with scrollbar
		main_frame = ttk.Frame(self.root)
		main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

		# === CONTENT PATHS SECTION ===
		paths_frame = ttk.LabelFrame(main_frame, text="Content Paths", padding=10)
		paths_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

		# Frame for path controls
		controls_frame = ttk.Frame(paths_frame)
		controls_frame.pack(fill=tk.X, pady=(0, 10))

		# Path type selection (left side)
		ttk.Label(controls_frame, text="Type:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))

		self.path_type_var = tk.StringVar(value="content")
		type_combo = ttk.Combobox(controls_frame, textvariable=self.path_type_var, values=["content", "addons"], state="readonly", width=10)
		type_combo.grid(row=0, column=1, padx=(0, 10))

		# Path entry (center)
		ttk.Label(controls_frame, text="Path:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))

		self.path_entry = ttk.Entry(controls_frame, width=40)
		self.path_entry.grid(row=0, column=3, padx=(0, 5), sticky=tk.EW)

		# Browse and Add buttons (right side)
		self.browse_button = ttk.Button(controls_frame, text="Browse", command=self.browse_path)
		self.browse_button.grid(row=0, column=4, padx=(0, 5))

		add_button = ttk.Button(controls_frame, text="Add", command=self.add_path)
		add_button.grid(row=0, column=5)

		# Grid configuration - make path entry expandable
		controls_frame.columnconfigure(3, weight=1)

		# Paths list
		list_frame = ttk.Frame(paths_frame)
		list_frame.pack(fill=tk.BOTH, expand=True)

		# Treeview to display paths
		columns = ("Type", "Path", "Status")
		self.paths_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=8)

		# Column configuration
		self.paths_tree.heading("Type", text="Type")
		self.paths_tree.heading("Path", text="Path")
		self.paths_tree.heading("Status", text="Status")

		self.paths_tree.column("Type", width=80, minwidth=80)
		self.paths_tree.column("Path", width=400, minwidth=200)
		self.paths_tree.column("Status", width=100, minwidth=80)

		# Scrollbar for list
		scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.paths_tree.yview)
		self.paths_tree.configure(yscrollcommand=scrollbar.set)

		self.paths_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
		scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

		# List buttons
		list_buttons_frame = ttk.Frame(paths_frame)
		list_buttons_frame.pack(fill=tk.X, pady=(10, 0))

		ttk.Button(list_buttons_frame, text="Remove", command=self.remove_selected_path).pack(side=tk.LEFT, padx=(0, 5))
		ttk.Button(list_buttons_frame, text="Refresh", command=self.refresh_paths_list).pack(side=tk.LEFT, padx=(0, 5))

		# === DRAG & DROP SECTION ===
		drop_frame = ttk.LabelFrame(main_frame, text="VMF Extraction", padding=10)
		drop_frame.pack(fill=tk.X, pady=(0, 10))

		# Drag & drop zone
		drop_text = "Drag & drop a .vmf file here or click to browse"
		if not HAS_DND:
			drop_text = "Click to select a .vmf file"

		self.drop_zone = tk.Label(drop_frame, text=drop_text, relief=tk.SUNKEN, height=4, justify=tk.CENTER, wraplength=700)
		self.drop_zone.pack(fill=tk.X, pady=(0, 10))
		self.drop_zone.bind("<Button-1>", self.on_drop_zone_click)

		# Extract button (initially disabled)
		self.extract_button = ttk.Button(drop_frame, text="Select a VMF file first", command=self.start_extraction, state="disabled")

		# Always show the button with same width as drop zone
		self.extract_button.pack(pady=(10, 0), fill=tk.X)

		# === LOG SECTION ===
		log_frame_container = ttk.LabelFrame(main_frame, text="Extraction Log", padding=10)
		log_frame_container.pack(fill=tk.BOTH, expand=True)

		log_frame = ttk.Frame(log_frame_container)
		log_frame.pack(fill=tk.BOTH, expand=True)

		self.log_text = tk.Text(log_frame, height=8, wrap=tk.WORD)
		log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
		self.log_text.configure(yscrollcommand=log_scrollbar.set)

		self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
		log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

	def setup_drag_drop(self):
		if HAS_DND:
			for widget in [self.root, self.drop_zone]:
				widget.drop_target_register(DND_FILES)
				widget.dnd_bind('<<Drop>>', self.on_file_drop)
		self.drop_zone.bind("<Button-1>", self.on_drop_zone_click)

	def browse_path(self):
		if path := filedialog.askdirectory(title="Select content folder"):
			self.path_entry.delete(0, tk.END)
			self.path_entry.insert(0, path)

	def add_path(self):
		path = self.path_entry.get().strip()
		if not path:
			return messagebox.showerror("Error", "Please select a path")
		if not os.path.exists(path):
			return messagebox.showerror("Error", f"Path does not exist: {path}")

		self.path_manager.add_path(path, self.path_type_var.get())
		self.path_entry.delete(0, tk.END)
		self.refresh_paths_list()
		self.log(f"Path added: {path} ({self.path_type_var.get()})")

	def remove_selected_path(self):
		if not (selection := self.paths_tree.selection()):
			return messagebox.showwarning("Warning", "Please select a path to remove")
			
		self.path_manager.remove_path(self.paths_tree.index(selection[0]))
		self.refresh_paths_list()
		self.log("Path removed")

	def refresh_paths_list(self):
		self.paths_tree.delete(*self.paths_tree.get_children())
		
		for path, path_type in self.path_manager.paths:
			status = "✓ Valid" if os.path.exists(path) else "✗ Not found"
			self.paths_tree.insert("", tk.END, values=(path_type.upper(), path, status))

	def on_file_drop(self, event):
		if event.data:
			files = self.root.tk.splitlist(event.data)
			if files:
				file_path = files[0]
				if file_path.lower().endswith('.vmf'):
					self.set_selected_vmf(file_path)
				else:
					messagebox.showerror("Error", "Please drop a .vmf file")

	def on_drop_zone_click(self, event):
		if self.selected_vmf:
			self.start_extraction()
		else:
			self.select_vmf_file()

	def select_vmf_file(self, event=None):
		file_path = filedialog.askopenfilename(title="Select VMF file", filetypes=[("VMF files", "*.vmf"), ("All files", "*.*")])
		if file_path:
			self.set_selected_vmf(file_path)

	def set_selected_vmf(self, file_path):
		self.selected_vmf = file_path
		vmf_name = os.path.basename(file_path)

		self.drop_zone.config(text=f"✅ Selected: {vmf_name}", relief=tk.RAISED)
		self.extract_button.config(text=f"Extract {vmf_name}", state="normal")

		self.log(f"VMF file selected: {vmf_name}")

	def start_extraction(self):
		if not self.selected_vmf:
			return messagebox.showwarning("Warning", "Please select a VMF file first!")
		if self.extraction_running:
			return messagebox.showwarning("Warning", "Extraction already in progress")
		self.extract_vmf(self.selected_vmf)

	def extract_vmf(self, vmf_path):
		if self.extraction_running:
			return messagebox.showwarning("Warning", "Extraction already in progress")

		content_paths = self.path_manager.get_all_content_paths()
		if not content_paths:
			return messagebox.showerror("Error", "No content paths configured.\nAdd at least one 'content' or 'addons' path.")

		thread = threading.Thread(target=self._extract_vmf_thread, args=(vmf_path, content_paths), daemon=True)
		thread.start()

	def _extract_vmf_thread(self, vmf_path, content_paths):
		try:
			self.extraction_running = True
			self.root.after(0, lambda: self.extract_button.config(state="disabled"))

			vmf_name = os.path.splitext(os.path.basename(vmf_path))[0]
			output_dir = f"extracted_{vmf_name}"

			self.log_async(f"Starting extraction: {vmf_name}")
			self.log_async(f"Content paths: {len(content_paths)}")

			self.log_async("Parsing VMF file...")
			parser = VMFParser()
			if not parser.parse_file(vmf_path):
				raise Exception("Unable to parse VMF file")

			mat_extractor = MaterialExtractor(content_paths)
			mdl_extractor = ModelExtractor(content_paths)
			sound_extractor = SoundExtractor(content_paths)

			self._extract_materials(parser, mat_extractor, output_dir)
			self._extract_skybox(parser, mat_extractor, output_dir)
			self._extract_models(vmf_path, mdl_extractor, mat_extractor, output_dir)
			self._extract_sounds(vmf_path, sound_extractor, output_dir)

			self._create_missing_file(output_dir, mat_extractor, mdl_extractor, sound_extractor)

			self.log_async(f"Extraction complete! Folder: {output_dir}")
			self.root.after(0, lambda: messagebox.showinfo("Success", f"Extraction complete!\n\nContent extracted to:\n{os.path.abspath(output_dir)}"))

		except Exception as e:
			error_msg = f"Extraction error: {e}"
			self.log_async(error_msg)
			self.root.after(0, lambda: messagebox.showerror("Error", error_msg))

		finally:
			self.extraction_running = False
			self.root.after(0, self.reset_drop_zone)

	def log_async(self, message):
		self.root.after(0, lambda: self.log(message))

	# Extract materials from VMF
	def _extract_materials(self, parser, mat_extractor, output_dir):
		self.log_async("Extracting materials...")
		materials = parser.get_all_materials()
		if materials:
			material_files = mat_extractor.find_files(materials)
			if material_files:
				mat_extractor.copy_to_directory(material_files, output_dir, True)
			self.log_async(f"Materials: {len(material_files)} found, {len(mat_extractor.missing)} missing")

	# Extract skybox materials from VMF
	def _extract_skybox(self, parser, mat_extractor, output_dir):
		self.log_async("Extracting skybox...")
		skybox_materials = parser.get_skybox_materials()
		if skybox_materials:
			skybox_files = mat_extractor.find_files(skybox_materials)
			if skybox_files:
				mat_extractor.copy_to_directory(skybox_files, output_dir, True)
			self.log_async(f"Skybox: {len(skybox_files)} found, {len(skybox_materials) - len(skybox_files)} missing")
		else:
			self.log_async("Skybox: No skybox defined in worldspawn")

	# Extract models from VMF
	def _extract_models(self, vmf_path, mdl_extractor, mat_extractor, output_dir):
		self.log_async("Extracting models...")
		models = mdl_extractor.extract_from_vmf(vmf_path)
		if models:
			model_files = mdl_extractor.find_files(models)
			if model_files:
				mdl_extractor.copy_to_directory(model_files, output_dir, True)
			self.log_async(f"Models: {len(model_files)} found, {len(mdl_extractor.missing)} missing")

			# Extract materials from models
			self.log_async("Extracting materials from models...")
			model_materials = mdl_extractor.extract_materials(model_files)
			if model_materials:
				model_material_files = mat_extractor.find_files(model_materials)
				if model_material_files:
					mat_extractor.copy_to_directory(model_material_files, output_dir, True)
				self.log_async(f"Model materials: {len(model_material_files)} found, {len(mat_extractor.missing)} missing")

	# Extract sounds from VMF
	def _extract_sounds(self, vmf_path, sound_extractor, output_dir):
		self.log_async("Extracting sounds...")
		sounds = sound_extractor.extract_from_vmf(vmf_path)
		if sounds:
			sound_files = sound_extractor.find_files(sounds)
			if sound_files:
				sound_extractor.copy_to_directory(sound_files, output_dir, True)

			self.log_async(f"Sounds: {len(sound_files)} found, {len(sound_extractor.missing)} missing")

	def reset_drop_zone(self):
		self.selected_vmf = None

		drop_text = "Drag & drop a .vmf file here or click to browse"
		if not HAS_DND:
			drop_text = "Click to select a .vmf file"

		self.drop_zone.config(text=drop_text, relief=tk.SUNKEN)
		self.extract_button.config(text="Select a VMF file first", state="disabled")

	def log(self, message):
		self.log_text.insert(tk.END, f"{message}\n")
		self.log_text.see(tk.END)

	def _create_missing_file(self, output_dir, mat_extractor, mdl_extractor, sound_extractor):
		try:
			missing_file_path = os.path.join(output_dir, "missing.txt")

			with open(missing_file_path, 'w', encoding='utf-8') as f:
				f.write("VMF Content Extractor - Missing Files Report\n")
				f.write("=" * 50 + "\n\n")

				# Missing materials
				if mat_extractor.missing:
					f.write(f"MISSING MATERIALS ({len(mat_extractor.missing)}):\n")
					f.write("-" * 30 + "\n")
					for material in sorted(mat_extractor.missing):
						f.write(f"materials/{material}.vmt\n")
					f.write("\n")

				# Missing models
				if mdl_extractor.missing:
					f.write(f"MISSING MODELS ({len(mdl_extractor.missing)}):\n")
					f.write("-" * 25 + "\n")
					for model in sorted(mdl_extractor.missing):
						f.write(f"models/{model}\n")
					f.write("\n")

				# Missing sounds
				if sound_extractor.missing:
					f.write(f"MISSING SOUNDS ({len(sound_extractor.missing)}):\n")
					f.write("-" * 25 + "\n")
					for sound in sorted(sound_extractor.missing):
						f.write(f"sound/{sound}\n")
					f.write("\n")

				# Summary
				total_missing = len(mat_extractor.missing) + len(mdl_extractor.missing) + len(sound_extractor.missing)
				f.write(f"SUMMARY:\n")
				f.write("-" * 15 + "\n")
				f.write(f"Total missing files: {total_missing}\n")
				f.write(f"- Materials: {len(mat_extractor.missing)}\n")
				f.write(f"- Models: {len(mdl_extractor.missing)}\n")
				f.write(f"- Sounds: {len(sound_extractor.missing)}\n")

			if total_missing > 0:
				self.root.after(0, lambda: self.log(f"Missing files report saved: missing.txt ({total_missing} items)"))
			else:
				if os.path.exists(missing_file_path):
					os.remove(missing_file_path)
				self.root.after(0, lambda: self.log("All files found! No missing.txt needed."))

		except Exception as e:
			self.root.after(0, lambda: self.log(f"Error creating missing.txt: {e}"))


def main():
	root = TkinterDnD.Tk() if HAS_DND else tk.Tk()
	VMFExtractorGUI(root)

	try:
		root.mainloop()
	except KeyboardInterrupt:
		pass


if __name__ == "__main__":
	main()