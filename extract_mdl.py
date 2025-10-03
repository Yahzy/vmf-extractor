import os
import shutil
from typing import Set, List, Dict, Optional
from parser_vmf import VMFParser
from parser_mdl import MDLParser


class ModelExtractor:
	# Init variables
	def __init__(self, directories: List[str] = None):
		self.directories = directories or []
		self.missing: Set[str] = set()
		self.extensions = ['.mdl', '.vvd', '.vtx', '.phy', '.ani', '.dx90.vtx', '.dx80.vtx']
		self.entities = [
			'prop_static', 'prop_dynamic', 'prop_dynamic_override',
			'prop_physics', 'prop_physics_multiplayer', 'prop_ragdoll',
			'prop_door_rotating', 'prop_button',
			'cycler', 'monster_*', 'npc_*', 'weapon_*', 'item_*'
		]

	# Extract all model paths from VMF
	def extract_from_vmf(self, vmf_path: str) -> Set[str]:
		parser = VMFParser()
		if not parser.parse_file(vmf_path):
			return set()

		models = set()
		for entity in parser.entities:
			if self._is_entity(entity.classname):
				model_path = self._extract_from_entity(entity)
				if model_path:
					models.add(model_path)

		return models

	# Check if entity is a model entity
	def _is_entity(self, classname: str) -> bool:
		classname_lower = classname.lower()

		for entity_type in self.entities:
			if entity_type.endswith('*'):
				if classname_lower.startswith(entity_type[:-1]):
					return True
			elif classname_lower == entity_type:
				return True

		return False

	# Extract model path from entity properties
	def _extract_from_entity(self, entity) -> Optional[str]:
		model_properties = ['model', 'file', 'ModelName', 'gibmodel', 'deadmodel']

		for prop in model_properties:
			value = entity.properties.get(prop)
			if value and value.lower().endswith('.mdl'):
				return value.replace('\\', '/').lower()
		
		return None

	# Find model files on disk
	def find_files(self, model_paths: Set[str]) -> Dict[str, Dict[str, str]]:
		found_files = {}

		for model_path in model_paths:
			files = self._find_single_files(model_path)
			if files:
				found_files[model_path] = files
			else:
				self.missing.add(model_path)

		return found_files

	# Find all associated model files for a single model path
	def _find_single_files(self, model_path: str) -> Dict[str, str]:
		clean_path = model_path.lower().replace('\\', '/')
		base_path = clean_path[:-4] if clean_path.endswith('.mdl') else clean_path
		files = {}

		for game_dir in self.directories:
			for ext in self.extensions:
				file_path = os.path.join(game_dir, base_path + ext)
				if os.path.exists(file_path):
					files[ext] = file_path

		return files

	# Extract materials used by models
	def extract_materials(self, model_files: Dict[str, Dict[str, str]]) -> Set[str]:
		materials = set()
		mdl_parser = MDLParser()

		for files in model_files.values():
			if '.mdl' in files:
				materials.update(mdl_parser.extract_materials_from_mdl(files['.mdl']))

		return materials


	# Copy found model files to output directory
	def copy_to_directory(self, model_files: Dict[str, Dict[str, str]], output_dir: str, preserve_structure: bool = True):
		os.makedirs(output_dir, exist_ok=True)

		for files in model_files.values():
			for file_path in files.values():
				try:
					if preserve_structure:
						dest_path = os.path.join(output_dir, self._get_relative_path(file_path))
						os.makedirs(os.path.dirname(dest_path), exist_ok=True)
					else:
						dest_path = os.path.join(output_dir, os.path.basename(file_path))

					shutil.copy2(file_path, dest_path)
				except Exception:
					pass

	# Get relative path for model files
	def _get_relative_path(self, file_path: str) -> str:
		parts = file_path.replace('\\', '/').split('/')
		try:
			idx = parts.index("models")
			return '/'.join(parts[idx:])
		except ValueError:
			return os.path.basename(file_path)