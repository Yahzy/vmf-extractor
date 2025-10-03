import os
import shutil
from typing import Set, List, Dict, Optional
from parser_vmf import VMFParser


class SoundExtractor:
	# Init variables
	def __init__(self, directories: List[str] = None):
		self.directories = directories or []
		self.missing: Set[str] = set()
		self.extensions = ['.wav', '.mp3', '.ogg']
		self.entities = [
			'func_door', 'func_door_rotating',
			'func_button',
			'prop_door_rotating',
			'func_train', 'func_tracktrain',
			'func_tanktrain',
			'func_rotating', 'ambient_generic', 'env_speaker',
		]
		self.properties = [
			# func_door & func_door_rotating
			'noise1', 'noise2',
			'closesound', 'startclosesound',
			'unlocked_sound', 'locked_sound', # also func_button

			# prop_door_rotating
			'soundopenoverride', 'soundcloseoverride', 'soundmoveoverride',
			'soundunlockedoverride', 'soundlockedoverride',

			# func_train & func_tracktrain
			'sound_moving', 'sound_stopping',

			# func_tanktrain
			'MoveSound', 'StopSound',

			# func_rotating & ambient_generic & env_speaker
			'message',
		]

	# Extract all sound paths from VMF
	def extract_from_vmf(self, vmf_path: str) -> Set[str]:
		parser = VMFParser()
		if not parser.parse_file(vmf_path):
			return set()

		sounds = set()
		for entity in parser.entities:
			if self._is_entity(entity.classname):
				sound_paths = self._extract_from_entity(entity)
				sounds.update(sound_paths)
			else:
				sound_paths = self._extract_from_properties(entity.properties)
				sounds.update(sound_paths)

		return sounds

	# Check if entity is a sound-related entity
	def _is_entity(self, classname: str) -> bool:
		classname_lower = classname.lower()
		return any(classname_lower == entity_type or classname_lower.startswith(entity_type) 
				   for entity_type in self.entities)

	# Extract sound paths from entity properties
	def _extract_from_entity(self, entity) -> Set[str]:
		return self._extract_from_properties(entity.properties)

	# Extract sound paths from properties dictionary
	def _extract_from_properties(self, properties: Dict[str, str]) -> Set[str]:
		sounds = set()
		prop_names_lower = [p.lower() for p in self.properties]

		for prop_name, prop_value in properties.items():
			if prop_name.lower() in prop_names_lower and prop_value and self._is_audio_file(prop_value):
				clean_path = prop_value.replace('\\', '/').lower()
				sounds.add(clean_path[1:] if clean_path.startswith('*') else clean_path)

		return sounds

	# Check if file has a valid audio extension
	def _is_audio_file(self, filepath: str) -> bool:
		return filepath and any(filepath.lower().endswith(ext) for ext in self.extensions)

	# Find sound files on disk
	def find_files(self, sound_paths: Set[str]) -> Dict[str, str]:
		found_files = {}

		for sound_path in sound_paths:
			file_path = self._find_single_file(sound_path)
			if file_path:
				found_files[sound_path] = file_path
			else:
				self.missing.add(sound_path)

		return found_files

	# Find single sound file on disk
	def _find_single_file(self, sound_path: str) -> Optional[str]:
		clean_path = sound_path.lower().replace('\\', '/')

		for game_dir in self.directories:
			paths_to_try = [
				os.path.join(game_dir, "sound", clean_path),
				os.path.join(game_dir, clean_path)
			]
			
			for path in paths_to_try:
				if os.path.exists(path):
					return path

			if '.' in clean_path:
				base_path = os.path.splitext(clean_path)[0]
				for ext in self.extensions:
					test_path = os.path.join(game_dir, "sound", base_path + ext)
					if os.path.exists(test_path):
						return test_path

		return None


	# Copy found sound files to output directory
	def copy_to_directory(self, sound_files: Dict[str, str], output_dir: str, preserve_structure: bool = True):
		os.makedirs(output_dir, exist_ok=True)

		for file_path in sound_files.values():
			try:
				if preserve_structure:
					dest_path = os.path.join(output_dir, self._get_relative_path(file_path))
					os.makedirs(os.path.dirname(dest_path), exist_ok=True)
				else:
					dest_path = os.path.join(output_dir, os.path.basename(file_path))

				shutil.copy2(file_path, dest_path)
			except Exception:
				pass

	# Get relative path for sound files
	def _get_relative_path(self, file_path: str) -> str:
		parts = file_path.replace('\\', '/').split('/')
		try:
			idx = parts.index("sound")
			return '/'.join(parts[idx:])
		except ValueError:
			return os.path.basename(file_path)