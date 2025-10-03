import struct
from typing import Set


class MDLParser:
	def __init__(self):
		pass

	# Extract materials from a MDL file
	def extract_materials_from_mdl(self, mdl_path: str) -> Set[str]:
		data = open(mdl_path, 'rb').read()

		return self._parse_mdl_simple(data)

	# Simple MDL parser to extract material names
	def _parse_mdl_simple(self, data: bytes) -> Set[str]:
		materials = set()

		try:
			if len(data) < 200 or data[0:4] != b'IDST':
				return materials

			offsets_to_try = [
				(204, 208, 212, 216),
				(148, 152, 156, 160),
				(200, 204, 208, 212),
				(220, 224, 228, 232),
			]

			best_result = set()

			for num_tex_offset, tex_idx_offset, num_cd_offset, cd_idx_offset in offsets_to_try:
				if len(data) < cd_idx_offset + 4:
					continue

				try:
					numtextures = struct.unpack('<I', data[num_tex_offset:num_tex_offset+4])[0]
					textureindex = struct.unpack('<I', data[tex_idx_offset:tex_idx_offset+4])[0]  
					numcdtextures = struct.unpack('<I', data[num_cd_offset:num_cd_offset+4])[0]
					cdtextureindex = struct.unpack('<I', data[cd_idx_offset:cd_idx_offset+4])[0]

					if (0 < numtextures <= 5000 and 0 < textureindex < len(data) and
						0 <= numcdtextures <= 1000 and (cdtextureindex == 0 or cdtextureindex < len(data))):

						current_materials = self._extract_textures_from_offsets(
							data, numtextures, textureindex, numcdtextures, cdtextureindex)

						if len(current_materials) > len(best_result):
							best_result = current_materials

				except Exception:
					continue

			materials.update(best_result)

		except Exception:
			pass

		return materials

	# Extract texture names from given offsets
	def _extract_textures_from_offsets(self, data: bytes, numtextures: int, textureindex: int, numcdtextures: int, cdtextureindex: int) -> Set[str]:
		materials = set()

		cd_directories = []
		if numcdtextures > 0 and cdtextureindex > 0 and cdtextureindex < len(data):
			for i in range(min(numcdtextures, 500)):
				cdtex_offset = cdtextureindex + (i * 4)

				if cdtex_offset + 4 <= len(data):
					nameoffset = struct.unpack('<I', data[cdtex_offset:cdtex_offset+4])[0]

					if 0 < nameoffset < len(data) - 4:
						name = self._read_null_terminated_string(data, nameoffset)
						if name and len(name) > 0 and self._is_valid_material_name(name):
							clean_name = name.lower().replace('\\', '/').rstrip('/')
							if len(clean_name) > 0:
								cd_directories.append(clean_name)

		texture_names = []
		if numtextures > 0 and textureindex > 0 and textureindex < len(data):
			for i in range(min(numtextures, 5000)):
				texture_offset = textureindex + (i * 64)

				if texture_offset + 64 <= len(data):
					sznameindex = struct.unpack('<I', data[texture_offset:texture_offset+4])[0]

					name_offsets_to_try = [
						texture_offset + sznameindex,
						sznameindex,
						textureindex + sznameindex,
					]

					for name_offset in name_offsets_to_try:
						if 0 < name_offset < len(data) - 4:
							name = self._read_null_terminated_string(data, name_offset)
							if name and len(name) > 0 and self._is_valid_material_name(name):
								clean_name = name.lower().replace('\\', '/')
								texture_names.append(clean_name)
								break

		if cd_directories and texture_names:
			for cd_dir in cd_directories:
				for texture_name in texture_names:
					if not texture_name.startswith('/'):
						full_path = f"{cd_dir}/{texture_name}"
					else:
						full_path = f"{cd_dir}{texture_name}"

					materials.add(full_path)

		return materials

	# Validate material name based on strict criteria
	def _is_valid_material_name(self, name: str) -> bool:
		if not name or len(name) < 2 or len(name) > 150:
			return False

		if not all(32 <= ord(c) <= 126 for c in name):
			return False

		allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-/\\')
		if not all(c in allowed_chars for c in name):
			return False

		alnum_count = sum(1 for c in name if c.isalnum())
		if alnum_count < len(name) * 0.3:
			return False

		bad_patterns = [
			'http', 'www', '.exe', '.dll', '.bat', '.cmd', 'system32', 
			'program files', 'windows', 'documents', 'temp', 'debug',
			'\\x', '\x00', '\xff', 'null', 'void', 'class', 'function'
		]
		name_lower = name.lower()
		if any(bad in name_lower for bad in bad_patterns):
			return False

		if name.startswith(('.', '-', '_', '\\', '/')) or name.endswith(('.', '-', '_')):
			return False

		if '//' in name or '\\\\' in name:
			return False

		return True

	# Read null-terminated ASCII string from data at given offset
	def _read_null_terminated_string(self, data: bytes, offset: int) -> str:
		if offset >= len(data):
			return ""

		end = offset
		while end < len(data) and data[end] != 0:
			if data[end] < 32 or data[end] > 126:
				return ""
			end += 1

		if end - offset < 2:
			return ""

		try:
			return data[offset:end].decode('ascii', errors='strict')
		except (UnicodeDecodeError, UnicodeError):
			return ""