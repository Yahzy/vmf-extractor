import re
from typing import Dict, List, Set, Optional
from dataclasses import dataclass


@dataclass
class VMFEntity:
	classname: str
	properties: Dict[str, str]
	id: Optional[str] = None


@dataclass
class VMFSide:
	material: str
	properties: Dict[str, str]


@dataclass
class VMFBrush:
	id: Optional[str]
	sides: List[VMFSide]


class VMFParser:
	# Init variables
	def __init__(self):
		self.entities: List[VMFEntity] = []
		self.brushes: List[VMFBrush] = []
		self.world_brushes: List[VMFBrush] = []

	# Parse VMF file
	def parse_file(self, vmf_path: str) -> bool:
		try:
			with open(vmf_path, 'r', encoding='utf-8', errors='ignore') as f:
				content = f.read()

			self._parse_content(content)
			return True

		except Exception as e:
			print(f"Error parsing VMF file: {e}")
			return False

	# Parse the content of the VMF file
	def _parse_content(self, content: str):
		lines = content.split('\n')
		lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith('//')]

		i = 0
		while i < len(lines):
			line = lines[i]

			if line == 'world':
				i = self._parse_world_section(lines, i + 1)
			elif line == 'entity':
				entity, i = self._parse_entity_section(lines, i + 1)
				if entity:
					self.entities.append(entity)
			else:
				i += 1

	# Parse the world section to extract brushes
	def _parse_world_section(self, lines: List[str], start_idx: int) -> int:
		i = start_idx

		if i < len(lines) and lines[i] == '{':
			i += 1

		brace_count = 1

		while i < len(lines) and brace_count > 0:
			line = lines[i]

			if line == '{':
				brace_count += 1
			elif line == '}':
				brace_count -= 1
			elif line == 'solid':
				brush, i = self._parse_brush_section(lines, i + 1)
				if brush:
					self.world_brushes.append(brush)
				continue

			i += 1

		return i

	# Parse an entity section to extract properties and brushes
	def _parse_entity_section(self, lines: List[str], start_idx: int) -> tuple[Optional[VMFEntity], int]:
		i = start_idx
		properties = {}
		brushes = []

		if i < len(lines) and lines[i] == '{':
			i += 1

		brace_count = 1

		while i < len(lines) and brace_count > 0:
			line = lines[i]

			if line == '{':
				brace_count += 1
			elif line == '}':
				brace_count -= 1
			elif line == 'solid':
				brush, i = self._parse_brush_section(lines, i + 1)
				if brush:
					brushes.append(brush)
				continue
			elif '"' in line:
				key, value = self._parse_property_line(line)
				if key and value:
					properties[key] = value

			i += 1

		classname = properties.get('classname')
		if classname:
			entity_id = properties.get('id')
			entity = VMFEntity(classname=classname, properties=properties, id=entity_id)

			self.brushes.extend(brushes)

			return entity, i

		return None, i

	# Parse a brush section to extract sides
	def _parse_brush_section(self, lines: List[str], start_idx: int) -> tuple[Optional[VMFBrush], int]:
		i = start_idx
		sides = []
		brush_id = None

		if i < len(lines) and lines[i] == '{':
			i += 1

		brace_count = 1

		while i < len(lines) and brace_count > 0:
			line = lines[i]

			if line == '{':
				brace_count += 1
			elif line == '}':
				brace_count -= 1
			elif line == 'side':
				side, i = self._parse_side_section(lines, i + 1)
				if side:
					sides.append(side)
				continue
			elif '"id"' in line:
				_, brush_id = self._parse_property_line(line)

			i += 1

		if sides:
			return VMFBrush(id=brush_id, sides=sides), i

		return None, i

	# Parse a side section to extract material and properties
	def _parse_side_section(self, lines: List[str], start_idx: int) -> tuple[Optional[VMFSide], int]:
		i = start_idx
		properties = {}

		if i < len(lines) and lines[i] == '{':
			i += 1

		brace_count = 1

		while i < len(lines) and brace_count > 0:
			line = lines[i]

			if line == '{':
				brace_count += 1
			elif line == '}':
				brace_count -= 1
			elif '"' in line:
				key, value = self._parse_property_line(line)
				if key and value:
					properties[key] = value

			i += 1

		material = properties.get('material', '')
		if material:
			return VMFSide(material=material, properties=properties), i

		return None, i

	# Parse a property line to extract key and value
	def _parse_property_line(self, line: str) -> tuple[Optional[str], Optional[str]]:
		match = re.match(r'"([^"]*)" "([^"]*)"', line)
		if match:
			return match.group(1), match.group(2)
		return None, None

	# Get all materials referenced
	def get_all_materials(self) -> Set[str]:
		materials = set()

		# Extract materials from brush faces (world geometry and entity brushes)
		for brush in self.world_brushes:
			for side in brush.sides:
				if side.material:
					materials.add(side.material.lower())

		for brush in self.brushes:
			for side in brush.sides:
				if side.material:
					materials.add(side.material.lower())

		# Extract materials from overlay and decal entities
		for entity in self.entities:
			# info_overlay entities use "material" property
			if entity.classname == 'info_overlay' and 'material' in entity.properties:
				material = entity.properties['material']
				if material:
					materials.add(material.lower())
			
			# infodecal entities use "texture" property
			elif entity.classname == 'infodecal' and 'texture' in entity.properties:
				texture = entity.properties['texture']
				if texture:
					materials.add(texture.lower())

		return materials

	# Get all models referenced
	def get_all_models(self) -> Set[str]:
		models = set()

		for entity in self.entities:
			model_props = ['model', 'file', 'ModelName', 'angles']

			for prop in model_props:
				if prop in entity.properties:
					value = entity.properties[prop]

					if value.endswith('.mdl'):
						models.add(value.lower())

		return models

	# Get all sounds referenced
	def get_all_sounds(self) -> Set[str]:
		sounds = set()

		for entity in self.entities:
			sound_props = ['message', 'sound', 'file', 'noise', 'soundfile']

			for prop in sound_props:
				if prop in entity.properties:
					value = entity.properties[prop]

					if any(value.lower().endswith(ext) for ext in ['.wav', '.mp3', '.ogg']):
						sounds.add(value.lower())

		return sounds