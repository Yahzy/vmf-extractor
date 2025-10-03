import os
import shutil
from typing import Set, List, Dict


class MaterialExtractor:
	# Init variables
	def __init__(self, directories: List[str] = None):
		self.directories = directories or []
		self.missing: Set[str] = set()

	# Find material files on disk
	def find_files(self, names: Set[str]) -> Dict[str, List[str]]:
		found_files = {}

		for name in names:
			files = self._find_single(name)
			if files:
				found_files[name] = files
			else:
				self.missing.add(name)

		return found_files

	# Find single material and associated textures
	def _find_single(self, name: str) -> List[str]:
		clean_name = name.lower().replace('\\', '/')

		for game_dir in self.directories:
			vmt_path = os.path.join(game_dir, "materials", clean_name + ".vmt")

			if os.path.exists(vmt_path):
				files = [vmt_path]
				files.extend(self._find_textures_from_vmt(vmt_path, game_dir))
				return files

		return []

	# Parse VMT file to find associated VTF textures
	def _find_textures_from_vmt(self, vmt_path: str, game_dir: str) -> List[str]:
		import re
		vtf_files = []

		try:
			with open(vmt_path, 'r', encoding='utf-8', errors='ignore') as f:
				content = f.read()

			patterns = [
				r'["\']?\$basetexture["\']?\s+["\']([^"\']+)["\']',
				r'["\']?\$basetexture["\']?\s+([^\s{}\[\]]+)',
				r'["\']?\$bumpmap["\']?\s+["\']([^"\']+)["\']',
				r'["\']?\$bumpmap["\']?\s+([^\s{}\[\]]+)',
				r'["\']?\$normalmap["\']?\s+["\']([^"\']+)["\']',
				r'["\']?\$normalmap["\']?\s+([^\s{}\[\]]+)',
				r'["\']?\$detail["\']?\s+["\']([^"\']+)["\']',
				r'["\']?\$detail["\']?\s+([^\s{}\[\]]+)',
				r'["\']?\$decaltexture["\']?\s+["\']([^"\']+)["\']',
				r'["\']?\$decaltexture["\']?\s+([^\s{}\[\]]+)',
			]

			for pattern in patterns:
				for match in re.findall(pattern, content, re.IGNORECASE):
					texture_name = match.strip().replace('\\', '/')

					if not texture_name or texture_name.lower() in ['env_cubemap', '_rt_camera']:
						continue

					for case_variant in [texture_name, texture_name.lower()]:
						vtf_path = os.path.join(game_dir, "materials", case_variant + ".vtf")
						if os.path.exists(vtf_path) and vtf_path not in vtf_files:
							vtf_files.append(vtf_path)
							break

		except Exception:
			pass

		return vtf_files

	# Copy found materials and textures to output directory
	def copy_to_directory(self, material_files: Dict[str, List[str]], output_dir: str, preserve_structure: bool = True):
		os.makedirs(output_dir, exist_ok=True)

		for file_paths in material_files.values():
			for file_path in file_paths:
				try:
					if preserve_structure:
						dest_path = os.path.join(output_dir, self._get_relative_path(file_path))
						os.makedirs(os.path.dirname(dest_path), exist_ok=True)
					else:
						dest_path = os.path.join(output_dir, os.path.basename(file_path))

					shutil.copy2(file_path, dest_path)
				except Exception:
					pass

	# Get relative path for material files
	def _get_relative_path(self, file_path: str) -> str:
		parts = file_path.replace('\\', '/').split('/')
		try:
			idx = parts.index("materials")
			return '/'.join(parts[idx:])
		except ValueError:
			return os.path.basename(file_path)