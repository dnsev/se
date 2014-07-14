#! /usr/bin/env python
# http://dnsev.github.io/se/
import os, re, sys, shutil, binascii, subprocess;
sub_edit_version = [ 1 , 2 ];



# Debug display
def display(json_var):
	import json;
	print json.dumps(json_var, indent=4, sort_keys=False);
	return None;



# Acquire track/attachment/etc. info about a file
def get_info(exe, filename, debug):
	# Return data
	ret = {
		"file": {},
		"tracks": [],
		"attachments": [],
		"chapters": 0
	};

	# Get info
	cmd = [ exe , "--identify-verbose" , filename ];
	try:
		p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE);
	except OSError:
		return None;
	c = p.communicate();

	# Debug
	if (debug):
		sys.stderr.write("Command:\n");
		sys.stderr.write("{0:s}\n".format(repr(cmd)));
		sys.stderr.write("Stdout:\n");
		sys.stderr.write("{0:s}\n".format(str(c[0])));
		sys.stderr.write("Stderr:\n");
		sys.stderr.write("{0:s}\n".format(str(c[1])));
		sys.stderr.write("Return: {0:d}\n\n".format(p.returncode));

	# Split
	line_pattern = regex_compile(r"\r\n?|\n");
	lines = line_pattern.split(c[0].strip());

	# Parsing patterns
	info_pattern = regex_compile(r"([^:]*?): (.*)");
	type_pattern = regex_compile(r"(File|Track|Attachment|Chapters)(?: ID ([0-9]+))?.*", re.I);
	file_pattern = regex_compile(r".*?\[(.*)\]");
	track_pattern = regex_compile(r"(\w+) \((.+?)\) \[(.*)\]");
	attachment_pattern = regex_compile(r"type '(.+?)', size ([0-9]+) bytes?, file name '(.+)'");
	chapters_pattern = regex_compile(r"([0-9]+) entr(?:y|ies)");

	# Parse
	for line in lines:
		# Line split
		m1 = info_pattern.match(line);
		if (m1 is None): continue;

		# Type info
		m2 = type_pattern.match(m1.group(1));
		if (m2 is None): continue;

		# Which type
		type = m2.group(1).lower();
		if (type == "file"):
			# File info
			m3 = file_pattern.match(m1.group(2));
			if (m3 is None): continue;

			# Get info
			ret["file"] = get_info_extra(m3.group(1));
		elif (type == "track"):
			# Track info
			m3 = track_pattern.match(m1.group(2));
			if (m3 is None): continue;

			id = -1;
			if (m2.group(2) is not None): id = int(m2.group(2));
			track = {
				"id": id,
				"type": m3.group(1),
				"info": m3.group(2),
				"extra": get_info_extra(m3.group(3))
			};
			ret["tracks"].append(track);
		elif (type == "attachment"):
			# Attachments
			m3 = attachment_pattern.match(m1.group(2));
			if (m3 is None): continue;

			attachment = {
				"type": m3.group(1),
				"size": int(m3.group(2)),
				"filename": m3.group(3)
			};
			ret["attachments"].append(attachment);
		elif (type == "chapters"):
			# Chapter info
			m3 = chapters_pattern.match(m1.group(2));
			if (m3 is None): continue;

			ret["chapters"] = int(m3.group(1));

	# Done
	return ret;

def get_info_extra(source):
	data = {};

	parts = source.split(" ");
	for i in range(len(parts)):
		keyval = parts[i].split(":");
		data[escape_info(keyval[0])] = escape_info(keyval[1]);

	return data;

def escape_info(value):
	new_val = "";
	escaped = False;
	for i in range(len(value)):
		c = value[i];
		if (escaped):
			# Escaped
			if (c == 's'): new_val += ' ';
			elif (c == '2'): new_val += '"';
			elif (c == 'c'): new_val += ':';
			elif (c == 'h'): new_val += '#';
			else: new_val += c; # backslash (and anything else)
			escaped = False;
		else:
			# Not escaped
			if (c == '\\'):
				escaped = True;
			else:
				new_val += c;

	return new_val;



# Unicode functions
def utf8_decode(byte_str):
	try:
		return byte_str.decode("utf-8");
	except:
		return byte_str;
def utf8_encode(text):
	try:
		return text.encode("utf-8");
	except:
		return text;
def regex_compile(pattern, flags=0):
	return re.compile(pattern, flags | re.U);



# Subtitle extraction
def extract_tracks(exe, filename, track_list, debug):
	# Setup track targets
	track_targets = [];
	for i in range(len(track_list)):
		track_targets.append(str(track_list[i]["id"]) + ":" + track_list[i]["filename"]);

	# Extract
	cmd = [ exe , "tracks" , filename ] + track_targets;
	try:
		p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE);
	except OSError:
		return False;
	c = p.communicate();

	# Debug
	if (debug):
		sys.stderr.write("Command:\n");
		sys.stderr.write("{0:s}\n".format(repr(cmd)));
		sys.stderr.write("Stdout:\n");
		sys.stderr.write("{0:s}\n".format(str(c[0])));
		sys.stderr.write("Stderr:\n");
		sys.stderr.write("{0:s}\n".format(str(c[1])));
		sys.stderr.write("Return: {0:d}\n\n".format(p.returncode));

	# Okay
	return True;

# Subtitle replacing/adding
def replace_subtitles(exe, filename, target, subtitle_files, debug):
	# Build command
	cmd = [ exe , "--output" , target , "-S" , filename ];
	for i in range(len(subtitle_files)):
		# Add tracks
		stf = subtitle_files[i];
		track_ids = [];
		cmd_extra = [];
		default_str = "true";
		for j in range(len(stf["tracks"])):
			prefix = "";
			if (stf["tracks"][j]["id"] is not None):
				prefix = str(stf["tracks"][j]["id"]);
				track_ids.append(prefix);
				prefix += ":";
				cmd_extra += [
					"--default-track" , prefix + default_str,
					"--forced-track" , prefix + default_str
				];
				default_str = "false";

			if (stf["tracks"][j]["title"] is not None):
				cmd_extra += [ "--track-name" , prefix + stf["tracks"][j]["title"] ];

			if (stf["tracks"][j]["language"] is not None):
				cmd_extra += [ "--language" , prefix + stf["tracks"][j]["language"] ];

		# Indicate file
		cmd += [ "-A" , "-D" , "-B" , "-M" ];
		if (len(track_ids) > 0):
			cmd += [ "--subtitle-tracks" , ",".join(track_ids) ];
		cmd += cmd_extra;
		cmd += [ stf["file"] ];

	# Extract
	try:
		p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE);
	except OSError:
		return False;
	c = p.communicate();

	# Debug
	if (debug):
		sys.stderr.write("Command:\n");
		sys.stderr.write("{0:s}\n".format(repr(cmd)));
		sys.stderr.write("Stdout:\n");
		sys.stderr.write("{0:s}\n".format(str(c[0])));
		sys.stderr.write("Stderr:\n");
		sys.stderr.write("{0:s}\n".format(str(c[1])));
		sys.stderr.write("Return: {0:d}\n\n".format(p.returncode));

	# Okay
	return True;



# Parsing a settings file
def parse_settings(settings_str, vars):
	# Split lines
	pattern = regex_compile(r"\r\n?|\n");
	settings = pattern.split(settings_str);
	modifiers = [];
	errors = [];
	var_pattern = regex_compile(r"@([^=]*)(?:=(.*))?")

	# Parse lines
	for i in range(len(settings)):
		# Parse line
		p = parse_settings_line(settings[i]);

		# Error check
		if (p["error"] is not None):
			# New error
			errors.append({
				"message": p["error"]["message"],
				"location": p["error"]["location"],
				"position": p["error"]["position"],
				"line": i,
			});
		else:
			# Check comment
			if (p["comment"] is not None):
				match = var_pattern.match(p["comment"]);
				if (match):
					var_name = match.group(1);
					var_value = match.group(2);
					if (var_name not in vars):
						# Error
						errors.append({
							"message": "Invalid variable name " + repr(var_name),
							"location": 2,
							"position": -1,
							"line": i,
						});
						continue;
					elif (var_value is None):
						# Error
						errors.append({
							"message": "Invalid variable value",
							"location": 2,
							"position": -1,
							"line": i,
						});
						continue;
					else:
						# Okay
						vars[var_name] = var_value;

			# Check key/value
			if (p["key"] is not None):
				# Remove comment
				p.pop("comment", None);

				# Setup regex if necessary
				if (p["regex_flags"] is None):
					# Convert to regex
					pat_str = "";
					# Before
					if (p["wildcards"][0][0]): pat_str += r"(\w*)";
					else: pat_str += r"(^|\W)";
					# Center
					pat_str += "(" + p["key"] + ")";
					# After
					if (p["wildcards"][0][1]): pat_str += r"(\w*)";
					else: pat_str += r"(\W|$)";

					# Compile
					flags = 0;
					if (p["flags"].find("?") < 0): flags = re.I;
					p["key"] = regex_compile(pat_str, flags);
					# Update wildcards
					p["wildcards"] = [
						not p["wildcards"][0][0] or p["wildcards"][1][0],
						not p["wildcards"][0][1] or p["wildcards"][1][1]
					];
				else:
					flags = 0;
					flag_str = p["regex_flags"].upper();
					for i in range(len(flag_str)):
						if (flag_str[i] == "I"): flags |= re.IGNORECASE;
						elif (flag_str[i] == "L"): flags |= re.LOCALE;
						elif (flag_str[i] == "M"): flags |= re.MULTILINE;
						elif (flag_str[i] == "S"): flags |= re.DOTALL;
						elif (flag_str[i] == "X"): flags |= re.VERBOSE;
						# Else, invalid

					try:
						p["key"] = regex_compile(p["key"], flags);
					except:
						# Error
						errors.append({
							"message": "Failed to compile regex expression",
							"location": 0,
							"position": -1,
							"line": i,
						});
						continue;

				# Add modifiers
				modifiers.append(p);

	# Done
	return [ modifiers , errors ];

def parse_settings_line(source):
	ret = {
		"error": None,
		"key": None,
		"value": None,
		"comment": None,
		"regex_flags": None,
		"parsable": False,
		"wildcards": None,
		"flags": None
	};

	# Get key
	part1 = parse_settings_value(source, 0, True, True, False, True, "");

	# Okay?
	if (part1["key"] is None):
		if (part1["error"] is not None):
			# Error
			ret["error"] = {
				"message": part1["error"],
				"location": 0,
				"position": part1["pos"],
			};
		elif (part1["reason"] == "comment"):
			# Comment only
			ret["comment"] = part1["comment"];
		elif (part1["reason"] != "end"):
			# Error
			ret["error"] = {
				"message": "Incomplete modifier",
				"location": 0,
				"position": part1["pos"],
			};
	else:
		# Get value
		is_regex = (part1["regex"] is not None);
		eol_characters = "";
		if (not is_regex): eol_characters = "!?";
		part2 = parse_settings_value(source, part1["pos"], False, not is_regex, is_regex, False, eol_characters);

		# Okay?
		if (part2["key"] is None):
			if (part2["error"] is not None):
				# Error
				ret["error"] = {
					"message": part2["error"],
					"location": 1,
					"position": part2["pos"],
				};
			else:
				# Comment only, or end of line
				ret["error"] = {
					"message": "Incomplete modifier",
					"location": 1,
					"position": part2["pos"],
				};
		else:
			# Okay
			ret["key"] = part1["key"];
			ret["value"] = part2["key"];
			ret["comment"] = part2["comment"];
			if (is_regex):
				ret["regex_flags"] = part1["regex"];
				ret["parsable"] = part2["quoted"];
			else:
				ret["wildcards"] = [ part1["asterisk"] , part2["asterisk"] ];
				ret["flags"] = part2["flags"];

	# Done
	return ret;

def parse_settings_value(source, i, regex_allowed, asterisk_allowed, parsable_str, find_arrow, eol_characters):
	asterisk = [ False , False ];

	i_max = len(source);

	ret = {
		"pos": 0,
		"reason": "",
		"comment": None,
		"error": None,
		"asterisk": asterisk,
		"key": None,
		"quoted": False,
		"regex": None,
		"flags": ""
	};

	# Before
	while (i < i_max):
		if (source[i] == '*' and asterisk_allowed):
			# Asterisk
			if (asterisk[0]):
				# Done
				break;
			else:
				# Pre-asterisk found
				asterisk[0] = True;
		elif (source[i] == '#'):
			# Comment
			ret["pos"] = i;
			ret["reason"] = "comment";
			ret["comment"] = source[i + 1 : ];
			if (asterisk[0]): ret["error"] = "Incomplete modifier";
			return ret;
		elif (ord(source[i]) > 32):
			# Not whitespace
			break;
		# Next
		i += 1;

	# End of string
	if (i >= i_max):
		ret["pos"] = i;
		ret["reason"] = "end";
		if (asterisk[0]): ret["error"] = "Incomplete modifier";
		return ret;


	# Find key
	key = "";
	arrow_found = False;
	is_regex = False;
	is_quoted = False;
	regex_modifiers = "";
	eol_flags = "";

	if (source[i] == '\'' or source[i] == '"'):
		# String
		quote = source[i];
		escaped = False;
		is_quoted = True;
		complete = False;
		i += 1;
		while (i < i_max):
			if (escaped):
				# Escape
				if (parsable_str):
					key += '\\' + source[i];
				else:
					key += source[i];
				escaped = False;
			else:
				if (source[i] == '\\'):
					# Update escape
					escaped = True;
				elif (source[i] == quote):
					# Done
					i += 1;
					complete = True;
					break;
				else:
					# Update
					key += source[i];
			# Next
			i += 1;

		# Error?
		if (not complete):
			ret["pos"] = i;
			ret["reason"] = "error";
			ret["error"] = "Incomplete string";
			return ret;

	elif (source[i] == '/' and regex_allowed):
		# Error?
		if (asterisk[0]):
			ret["pos"] = i;
			ret["reason"] = "syntax";
			ret["error"] = "Cannot have asterisk before a regex expression";
			return ret;

		# Regex
		quote = source[i];
		escaped = False;
		is_regex = True;
		complete = False;
		i += 1;
		while (i < i_max):
			if (escaped):
				# Escape
				key += '\\' + source[i];
				escaped = False;
			else:
				if (source[i] == '\\'):
					# Update escape
					escaped = True;
				elif (source[i] == quote):
					# Done
					i += 1;
					complete = True;
					break;
				else:
					# Update
					key += source[i];
			# Next
			i += 1;

		# Error?
		if (not complete):
			ret["pos"] = i;
			ret["reason"] = "error";
			ret["error"] = "Incomplete regex pattern";
			return ret;

		# Modifiers
		modifier_pattern = regex_compile(r"[a-zA-Z]");
		while (i < i_max):
			# Check if valid
			if (not modifier_pattern.match(source[i])):
				break;
			else:
				regex_modifiers += source[i];
			# Next
			i += 1;

	else:
		# Unquoted string
		while (i < i_max):
			if (source[i] == '#'):
				# Comment
				ret["pos"] = i;
				ret["reason"] = "comment";
				ret["comment"] = source[i + 1 : ];
				ret["error"] = "Incomplete modifier";
				return ret;
			elif (find_arrow and source[i] == '-' and i + 1 < i_max and source[i + 1] == '>'):
				# End
				i += 2;
				break;
			else:
				# Update string
				key += source[i];
			# Next
			i += 1;

		# Error?
		if (i >= i_max and find_arrow):
			ret["pos"] = i;
			ret["reason"] = "error";
			ret["error"] = "Incomplete modifier";
			return ret;

		# Find eol_characters
		j = len(key);
		asterisk_allowed2 = asterisk_allowed;
		while (True):
			# Next
			j -= 1;
			if (j < 0): break;

			# Check
			c = ord(key[j]);
			if (key[j] == '*' and asterisk_allowed2):
				# Set end asterisk
				asterisk[1] = True;
				j -= 1;
				break;
			elif (c > 32):
				if (eol_characters.find(key[j]) >= 0):
					# Update flags
					eol_flags += key[j];
					asterisk_allowed2 = False;
				else:
					# Stop
					break;

		# Update key
		j += 1;
		if (j < 0): j = 0;
		key = key[0 : j].strip();

		# Arrow included
		arrow_found = True;


	# Find arrow?
	if (find_arrow and not arrow_found):
		# After
		while (i < i_max):
			if (source[i] == '*' and asterisk_allowed):
				# Asterisk
				if (is_regex):
					# Error
					ret["pos"] = i;
					ret["reason"] = "syntax";
					ret["error"] = "Invalid asterisk found after regex";
					return ret;
				else:
					if (asterisk[1]):
						# Error
						ret["pos"] = i;
						ret["reason"] = "syntax";
						ret["error"] = "Invalid asterisk found";
						return ret;
					else:
						# Post-asterisk found
						asterisk[1] = True;
			elif (source[i] == '#'):
				# Comment
				ret["pos"] = i;
				ret["reason"] = "comment";
				ret["comment"] = source[i + 1 : ];
				ret["error"] = "Incomplete modifier";
				return ret;
			elif (source[i] == '-' and i + 1 < i_max and source[i + 1] == '>'):
				# Done
				i += 2;
				break;
			elif (ord(source[i]) > 32):
				# Error
				ret["pos"] = i;
				ret["reason"] = "syntax";
				ret["error"] = "Invalid character " + repr(source[i]) + " found";
				return ret;

			# Next
			i += 1;

		# Error?
		if (i >= i_max):
			ret["pos"] = i;
			ret["reason"] = "error";
			ret["error"] = "Incomplete modifier";
			return ret;


	# Key error
	if (len(key) == 0):
		ret["pos"] = i;
		ret["reason"] = "error";
		ret["error"] = "Invalid value";
		return ret;


	# Comment
	if (not find_arrow):
		while (i < i_max):
			if (source[i] == '#'):
				# Comment
				ret["comment"] = source[i + 1 : ];
				i = len(source);
				break;
			elif (ord(source[i]) > 32):
				if (eol_characters.find(source[i]) >= 0):
					# Flag
					eol_flags += source[i];
				else:
					# Error
					ret["pos"] = i;
					ret["reason"] = "syntax";
					ret["error"] = "Invalid character " + repr(source[i]) + " found";
					return ret;
			# Next
			i += 1;


	# Done
	ret["pos"] = i;
	ret["key"] = key;
	ret["quoted"] = is_quoted;
	ret["flags"] = eol_flags;
	if (is_regex): ret["regex"] = regex_modifiers;
	return ret;



# Modify
def apply_modifiers_to_file(filename, target, modifiers):
	# File type
	ext = os.path.splitext(filename)[1].lower();
	is_ass = (ext == ".ass" or ext == ".ssa");
	modifications = 0;

	# Open file
	try:
		f = open(filename, "rb");
	except IOError:
		return -1;
	try:
		fo = open(target, "wb");
	except IOError:
		f.close();
		return -1;

	# Which type
	if (is_ass):
		# .ass, .ssa
		pattern_ass_start = regex_compile(r"\[Events\]", re.I);
		pattern_ass_label = regex_compile(r"^([^\:]+):\s?");
		pattern_ass_format_split = regex_compile(r"\s*,\s*");
		start_found = False;
		format = None;
		format_pattern = None;

		# Read file
		while (True):
			# Read line
			line_full = utf8_decode(f.readline());
			remove_len = 0;
			if (len(line_full) > 0 and line_full[len(line_full) - 1] == '\n'):
				remove_len += 1;
				if (len(line_full) > 0 and line_full[len(line_full) - 2] == '\r'):
					remove_len += 1;

			# Done
			if (remove_len == 0): break;

			# Update line
			line_end = line_full[len(line_full) - remove_len : ];
			line = line_full[0 : len(line_full) - remove_len];

			# Update line
			if (start_found):
				# Format check
				m = pattern_ass_label.search(line);
				if (m is not None):
					line_start = m.end(0);
					if (format is None):
						if (m.group(1).lower() == "format"):
							# Compile the format pattern
							format = pattern_ass_format_split.split(line[line_start : ]);
							format_pattern = r"^(";
							for i in range(len(format) - 1):
								format_pattern += r"([^,]*),";
							format_pattern += r")(.*)$";
							format_pattern = regex_compile(format_pattern);
					else:
						# Test format
						m2 = format_pattern.match(line[line_start : ]);
						if (m2 is not None):
							# Replace
							line = m.group(0) + m2.group(1);

							# Format the line
							mods = apply_modifiers(m2.groups()[len(m2.groups()) - 1], modifiers);
							line += mods[0];
							modifications += mods[1];

				# Update line
				line_full = line + line_end;
			else:
				# Find start
				m = pattern_ass_start.match(line);
				if (m is not None):
					start_found = True;

			# Append line
			fo.write(utf8_encode(line_full));

	else:
		# .srt

		# Read file
		while (True):
			# Read line
			line_full = f.readline();
			remove_len = 0;
			if (len(line_full) > 0 and line_full[len(line_full) - 1] == '\n'):
				remove_len += 1;
				if (len(line_full) > 0 and line_full[len(line_full) - 2] == '\r'):
					remove_len += 1;

			# Done
			if (remove_len == 0): break;

			# Update line
			line_end = line_full[len(line_full) - remove_len : ];
			line = line_full[0 : len(line_full) - remove_len];

			# Update line
			mods = apply_modifiers(line, modifiers);
			line = mods[0];
			modifications += mods[1];

			# Append line
			fo.write(utf8_encode(line + line_end));

	# Done modifying
	f.close();
	fo.close();
	return modifications;

def apply_modifiers(text, modifiers):
	# New text
	new_text = text;
	modifications = 0;

	# Loop across modifiers
	for i in range(len(modifiers)):
		# Get modifier
		m = modifiers[i];

		if (m["regex_flags"] is None):
			# Find
			t = new_text;
			new_text = "";
			reg_exp = m["key"];
			match_case = (m["flags"].find("!") >= 0);
			while (True):
				# Find
				match = reg_exp.search(t);
				if (match is None): break;

				# Update
				new_text += t[0 : match.start(0)];
				if (m["wildcards"][0]): new_text += match.group(1);
				if (match_case): new_text += string_match_case(m["value"], match.group(2));
				else: new_text += m["value"];
				if (m["wildcards"][1]): new_text += match.group(3);
				modifications += 1;

				# Next
				t = t[match.end(0) : ];

			# Add end
			new_text += t;

		else:
			# Find
			t = new_text;
			new_text = "";
			reg_exp = m["key"];
			while (True):
				# Find
				match = reg_exp.search(t);
				if (match is None): break;

				# Update
				new_text += t[0 : match.start(0)];
				if (m["parsable"]): new_text += regex_match_string_replace(match, m["value"]);
				else: new_text += m["value"];
				modifications += 1;

				# Next
				t = t[match.end(0) : ];

			# Add end
			new_text += t;

	# Done
	return ( new_text , modifications );

# Perform a string replacement
def regex_match_string_replace(match, replacement):
	escaped = False;
	value = [ "" , "" ];
	id = 0;

	pattern = regex_compile(r"^([0-9]+)([CILPUXx]*)(?::(.*))?$");
	match_count = len(match.groups());

	for i in range(len(replacement)):
		if (escaped):
			# Escaped
			value[id] += replacement[i];
			escaped = False;
		else:
			if (replacement[i] == '\\'):
				# Escape
				escaped = True;
			elif (replacement[i] == '{' and id == 0):
				# Format region
				id = 1;
			elif (replacement[i] == '}' and id == 1):
				# End format region
				id = 0;

				# Apply format
				fm = pattern.match(value[1]);
				value[0] += regex_match_string_replace_part(match, pattern, value[1], match_count);

				# Clean format
				value[1] = "";
			else:
				# Add character
				value[id] += replacement[i];

	# Return
	return value[0] + value[1];

def regex_match_string_replace_part(match, pattern, text, max_id):
	fm = pattern.match(text);
	if (fm is None):
		# Bad format
		return "{" + text + ":bad-format}";
	else:
		# Replace
		fm_id = int(fm.group(1));
		if (fm_id > max_id):
			# Invalid id
			return "{" + text + ":bad-id}";
		else:
			# Flags
			if (fm.group(3) is None):
				# Direct replacement
				flag_str = fm.group(2);
				original = match.group(fm_id);

				if (original is None):
					original = "";

				if ("U" in flag_str):
					# Upper case
					original = original.upper();
				elif ("L" in flag_str):
					# Lower case
					original = original.lower();
				elif ("P" in flag_str):
					# Capitalize
					original = string_proper_case(original);
				elif ("C" in flag_str):
					# Capitalize
					original = string_capitalize(original);
				if ("I" in flag_str):
					# Inverse
					original = string_invert_case(original);

				# Return the (modified) match
				return original;
			else:
				# Replacement string
				flag_str = fm.group(2);
				original = match.group(fm_id);
				repl_str = fm.group(3);

				if (original is None):
					if ("X" in flag_str):
						# Omit
						return "";
					original = "";

				if ("x" in flag_str):
					# Omit
					return "";
				if ("U" in flag_str):
					# Upper case
					repl_str = repl_str.upper();
				elif ("L" in flag_str):
					# Lower case
					repl_str = repl_str.lower();
				elif ("P" in flag_str):
					# Lower case
					repl_str = string_proper_case(repl_str);
				elif ("C" in flag_str):
					# Capitalize
					repl_str = string_match_case(repl_str, original);
				if ("I" in flag_str):
					# Inverse
					repl_str = string_invert_case(repl_str);

				# Return the (modified) match
				return repl_str;



# Count the number of letters in text that match a regex
def regex_count(regex, text, inverse = False):
	count = 0;
	lt = len(text);

	while (True):
		m = regex.search(text);
		if (m is None): break;

		count += len(m.group(0));
		text = text[m.end(0) : ];

	if (inverse): count = lt - count;
	return count;

# Get filename component information
def parse_filename(filename):
	# Parts
	"""
		untagged:
			name
		tagged:
			name2
			file info
			group
			crc
	"""

	# Part pattern finder
	pattern = regex_compile(r"([^\[\(]*)(\[.+?\]|\(.+?\))|(.*)");
	pattern_info = regex_compile(r"(aac|flac|ogg|mp3)|([hx]\.?26[45]|8bit|10bit|hi10p?|xvid|divx)|(bd(?:\W?rip)?|blu\W?ray|tv(?:.?rip)?)|([0-9]+x[0-9]+|[0-9]+p?)", re.I);
	# 0: audio, 1: video, 2: release quality, 3: resolution
	pattern_info_separators = regex_compile(r"[\s,_-]+");
	pattern_group = regex_compile(r"[a-z0-9-_]+", re.I);
	pattern_crc = regex_compile(r"[a-z0-9]{8}", re.I);

	# Split into parts
	search = filename;
	parts = [];
	while (True):
		# Match
		match = pattern.search(search);
		if (match is None): break;

		# Last
		if (match.group(3) is not None):
			parts.append(match.group(3));
			break;

		# Add
		parts.append(match.group(1));
		tag = match.group(2);
		bracket = tag[0];
		tag = tag[1 : len(tag) - 1];
		parts.append([ tag , bracket ]);

		# Update
		search = search[match.end(0) : ];

	# Parse [tags]
	r_parts = [];
	i = 0;
	crc_count = 0;
	group_count = 0;
	info_count = 0;
	while (True):
		# Text
		if (len(parts[i]) > 0):
			r_parts.append({
				"type": "name",
				"value": parts[i],
				"container": None,
				"certainty": 1.0
			});

		# Next
		i += 1;
		if (i >= len(parts)): break;

		# Setup tag
		p = {
			"type": "name2",
			"value": parts[i][0],
			"container": "[]",
			"certainty": 0.0
		};
		if (parts[i][1] == "("): p["container"] = "()";
		tag = parts[i][0];

		# CRC
		if (len(tag) == 8 and pattern_crc.match(tag)):
			p["type"] = "crc";
			p["certainty"] = 1.0;
			if (tag.lower() != tag and tag.upper() != tag): p["certainty"] = 0.5;
			crc_count += 1;
		else:
			# Info check
			tag_temp = tag;
			tag_count = 0;
			tag_info_count = 0;
			while (True):
				m = pattern_info.search(tag_temp);
				if (m is None): break;

				# Count "correctness"
				tag_count += len(m.group(0)) + regex_count(pattern_info_separators, tag_temp[0 : m.start(0)]);
				tag_info_count += 1;
				tag_temp = tag_temp[m.end(0) : ];

			# Type check
			if (tag_info_count > 0):
				# Info
				tag_count += regex_count(pattern_info_separators, tag_temp);
				p["type"] = "info";
				p["certainty"] = tag_count / float(len(tag));
				info_count += 1;
			else:
				# Potentially a group
				p["type"] = "group";
				p["certainty"] = regex_count(pattern_group, tag) / float(len(tag));
				group_count += 1;

		# Next
		r_parts.append(p);
		i += 1;

	# Group settings
	if (group_count == 0):
		# No group
		new_id = -1;
		new_is_crc = True;

		if (crc_count > 0):
			# Convert a CRC to group
			any_id = -1;
			for i in range(len(r_parts)):
				if (r_parts[i]["type"] == "crc"):
					# Any
					if (
						any_id < 0 or
						(r_parts[any_id]["container"] != "[]" and r_parts[i]["container"] == "[]")
					):
						any_id = i;

					# Specific
					if (new_id < 0):
						if (r_parts[i]["certainty"] < 1.0):
							new_id = i;
					elif (r_parts[new_id]["container"] != "[]" and r_parts[i]["container"] == "[]"):
						new_id = i;
						break;

			# Test new_id
			if (new_id < 0 and crc_count > 1): new_id = any_id;

		elif (info_count > 1):
			# Convert an info to group
			new_is_crc = False;
			for i in range(len(r_parts)):
				if (r_parts[i]["type"] == "info"):
					# Id check
					if (
						r_parts[i]["certainty"] < 0.5 and
						(new_id < 0 or r_parts[i]["certainty"] < r_parts[new_id]["certainty"])
					):
						any_id = i;

		# Change new_id to a group
		if (new_id >= 0):
			r_parts[new_id]["type"] = "group";
			r_parts[new_id]["certainty"] = regex_count(pattern_group, r_parts[new_id]["value"]) / float(len(r_parts[new_id]["value"]));
			group_count += 1;
			if (new_is_crc): crc_count += 1;
			else: info_count += 1;

	elif (group_count > 1):
		# Too many groups
		most_id = -1;
		for i in range(len(r_parts)):
			if (r_parts[i]["type"] == "group"):
				# Test
				if (
					most_id < 0 or
					(r_parts[i]["certainty"] > r_parts[most_id]["certainty"]) or
					(
						r_parts[i]["certainty"] == r_parts[most_id]["certainty"] and
						r_parts[i]["container"] == "[]" and r_parts[most_id]["container"] != "[]"
					)
				):
					most_id = i;

		# Un-group all that aren't most_id
		for i in range(len(r_parts)):
			if (r_parts[i]["type"] == "group" and i != most_id):
				r_parts[i]["type"] = "name2";
				r_parts[i]["certainty"] = 1.0;


	# Return
	return r_parts;

# Get file
def change_filename(filename_parts, group_modifier, new_crc):
	# Convert crc to string
	if (new_crc is not None):
		new_crc = "{0:08x}".format(new_crc).upper();

		# Replace
		for i in range(len(filename_parts)):
			if (filename_parts[i]["type"] == "crc"):
				filename_parts[i]["value"] = new_crc;

	# Update group
	for i in range(len(filename_parts)):
		if (filename_parts[i]["type"] == "group"):
			filename_parts[i]["value"] = group_modifier.replace("*", filename_parts[i]["value"]);

	# Concat all
	new_filename = "";
	for i in range(len(filename_parts)):
		cont = filename_parts[i]["container"];
		if (cont is not None):
			new_filename += cont[0] + filename_parts[i]["value"] + cont[1];
		else:
			new_filename += filename_parts[i]["value"];

	# Return new
	return new_filename;

# Check if a filename has a CRC
def filename_has_crc(filename_parts):
	# Check
	for i in range(len(filename_parts)):
		if (filename_parts[i]["type"] == "crc"):
			return True;

	# Not found
	return False;



# Test to see if a string is "true"
def string_is_true(text):
	text = text.strip().lower();

	if (text == "true" or text == "yes" or text == "1"):
		return True;

	return False;

# Match the upper/lower-case-ness of a string to another
def string_match_case(text, target):
	# Remove non-alphabetic characters
	pattern_word = regex_compile(r"[a-zA-Z]+");
	pattern_lower = regex_compile(r"^[a-z]+$");
	pattern_upper = regex_compile(r"^[A-Z]+$");
	pattern_capital = regex_compile(r"^[A-Z][a-z]*$");

	# Get word cases
	word_cases = [];

	while (True):
		m = pattern_word.search(target);
		if (m is None): break;

		# Get case
		case = -1;
		if (pattern_lower.match(m.group(0)) is not None): case = 0;
		elif (pattern_upper.match(m.group(0)) is not None): case = 1;
		elif (pattern_capital.match(m.group(0)) is not None): case = 2;

		word_cases.append(case);

		# Next
		target = target[m.end(0) : ];

	if (len(word_cases) == 0): word_cases.append(0);

	# Update text
	t = "";
	i = 0;
	while (True):
		m = pattern_word.search(text);
		if (m is None): break;

		# Get word
		t += text[0 : m.start(0)];
		w = m.group(0);

		# Match case
		wc = word_cases[min(i, len(word_cases) - 1)];
		if (wc == 0):
			w = w.lower();
		elif (wc == 1):
			w = w.upper();
		elif (wc == 2):
			if (i == 0 or len(word_cases) > 1):
				w = w[0].upper() + w[1 : ];
			else:
				w = w.lower();
		else:
			# Default to lower
			w = w.lower();

		# Add word
		t += w;

		# Next
		text = text[m.end(0) : ];
		i += 1;

	# Done
	return t + text;

# Capitalize the first letter of a string
def string_capitalize(text):
	if (len(text) == 0): return text;

	return text[0].upper() + text[1 : ].lower();

# Capitalize the first letter of each word
def string_proper_case(text):
	# Compile a pattern
	pattern = regex_compile(r"[a-zA-Z]+");

	# Run word replacement
	return pattern.sub(string_proper_case_replacer, text);
def string_proper_case_replacer(match):
	return string_capitalize(match.group(0));

# Invert the case of a string
def string_invert_case(text):
	t = "";
	c_a = ord('a');
	c_z = ord('z');
	c_A = ord('A');
	c_Z = ord('Z');

	for i in range(len(text)):
		c = ord(text[i]);
		if (c >= c_a and c <= c_z):
			t += chr(c + c_A - c_a);
		elif (c >= c_A and c <= c_Z):
			t += chr(c + c_a - c_A);
		else:
			t += text[i];

	return t;



# Get file CRC
def get_file_crc(filename):
	crc = 0;
	# Open file
	try:
		f = open(filename, "rb");
	except IOError:
		return None;

	# Loop
	read_size = 1024 * 10;
	while (True):
		data = f.read(read_size);
		if (len(data) == 0): break;

		crc = binascii.crc32(data, crc);

	# Return
	f.close();
	return crc & 0xffffffff;

# Get a unique file name
def get_unique_filename(path, filename, suffix, id_start = 0, id_prefix = "[" , id_suffix = "]", id_limit = -1):
	# Setup
	fn = filename + suffix;
	fn_full = os.path.join(path, fn);

	has_limit = (id_limit > id_start);

	while (os.path.exists(fn_full)):
		# Update filename
		fn = filename + id_prefix + str(id_start) + id_suffix + suffix;
		fn_full = os.path.join(path, fn);

		# Update id
		id_start += 1;

		# Limit
		if (has_limit and id_start >= id_limit): break;

	# Done
	return fn_full;



# Check for exe versions
def update_exe_data(exe_data):
	# Return false if already checked
	if (exe_data["checked"]): return False;

	# Check
	fn = exe_data["filename"];
	found = False;
	script_dir = os.path.dirname(os.path.realpath(__file__));
	fn_list = [
		os.path.join(script_dir, fn + ".exe"),
		fn + ".exe",
	];

	for i in range(len(fn_list)):
		if (os.path.exists(fn_list[i]) and os.path.isfile(fn_list[i])):
			found = True;
			exe_data["filename"] = fn_list[i];
			break;

	# Done checking
	exe_data["checked"] = True;
	return found;



# Main execution
def main():
	# Usage
	if (len(sys.argv) <= 1):
		info = [
			"Usage:\n",
			"    {0:s} [settings_file.txt] input1.mkv [input2.mkv] ...\n\n".format(os.path.split(sys.argv[0])[1]),
			"    settings_file.txt\n",
			"        An optional file containing the replacement settings\n",
			"        If omitted, it defaults to <script_directory>/settings.txt\n\n",
			"    input1.mkv\n",
			"        A .mkv file containing subtitles to modify\n",
			"        Can also be a single .ass, .ssa, or .srt subtitles file\n\n",
			"    input2.mkv ...\n",
			"        Specify multiple files to process at once by adding more file names\n\n\n",
			"For more information, check readme.html\n",
		];
		sys.stdout.write("".join(info));

		return 0;



	# Paramters
	filenames = [];
	settings_file = None;
	settings_vars = {
		"group": "*-Sedit",
		"crc": "true",
		"script": "* [SubEdited]",
		"internal": "true",
		"keep_original": "true",
		"debug": "false"
	};
	settings_vars_overwritten = {};
	valid_extensions = [ ".txt" , ".mkv" , ".mk3d" , ".mks" , ".ass" , ".ssa" , ".srt" ]
	valid_mkv_extensions = [ ".mkv" , ".mk3d" , ".mks" ];



	# Parse arguments
	i = 1;
	i_max = len(sys.argv);
	errors = [];
	while (i < i_max):
		arg = sys.argv[i];
		if (len(arg) == 0 or arg[0] != '-'):
			# Normal argument
			ext = os.path.splitext(arg)[1].lower();
			if (ext in valid_extensions):
				if (ext == ".txt"):
					# Settings
					settings_file = arg;
				else:
					# Subtitle'd file
					filenames.append(arg);
			else:
				# Error
				errors.append("Invalid file extension for {0:s}".format(arg));
		elif (len(arg) == 1 or arg[1] != '-'):
			# - Flag
			flag = arg[1 : ];
			if (flag in [ "s" , "settings" ]):
				i += 1;
				if (i < i_max):
					# Set
					settings_file = sys.argv[i];
				else:
					# Error
					errors.append("Expected a value for -{0:s}".format(flag));
			elif (flag in [ "se" , "settings_if_exists" ]):
				i += 1;
				if (i < i_max):
					# Set
					if (os.path.exists(sys.argv[i])):
						settings_file = sys.argv[i];
				else:
					# Error
					errors.append("Expected a value for -{0:s}".format(flag));
			elif (flag in [ "i" , "input" ]):
				i += 1;
				if (i < i_max):
					# Set
					filenames.append(sys.argv[i]);
				else:
					# Error
					errors.append("Expected a value for -{0:s}".format(flag));
			elif (flag in [ "ie" , "input_if_exists" ]):
				i += 1;
				if (i < i_max):
					# Set
					if (os.path.exists(sys.argv[i])):
						filenames.append(sys.argv[i]);
				else:
					# Error
					errors.append("Expected a value for -{0:s}".format(flag));
			elif (flag in [ "v" , "version" ]):
				# Display version and exit
				str_version = "";
				for j in range(len(sub_edit_version)):
					if (j > 0): str_version += ".";
					str_version += str(sub_edit_version[j]);
				sys.stdout.write("Version {0:s}\n".format(str_version));
				return 0;
			else:
				# Error
				errors.append("Invalid flag -{0:s}".format(flag));
		else:
			# -- Flag
			flag = arg[2 : ];
			if (flag in settings_vars):
				i += 1;
				if (i < i_max):
					# Set
					settings_vars[flag] = sys.argv[i];
					settings_vars_overwritten[flag] = True;
				else:
					# Error
					errors.append("Expected a value for --{0:s}".format(flag));
			else:
				# Error
				errors.append("Invalid settings flag --{0:s}".format(flag));

		# Next
		i += 1;



	# Errors
	if (len(errors) > 0):
		sys.stderr.write("Encountered {0:d} error{1:s} parsing the command line:\n".format(len(errors), "" if len(errors) == 0 else "s"));
		for i in range(len(errors)):
			sys.stderr.write("    {0:s}\n".format(errors[i]));

		return -1;



	# No files
	if (len(filenames) == 0):
		sys.stderr.write("No input files given\n");

		return 1;



	# Modify
	if (settings_file is None):
		# Search current directory, then script directory
		settings_file_default_name = "settings.txt";
		settings_file = os.path.abspath(settings_file_default_name);
		if (not os.path.exists(settings_file)):
			# Check script dir
			script_dir = os.path.dirname(os.path.realpath(__file__));
			settings_file = os.path.join(script_dir, settings_file_default_name);
	settings_file = os.path.abspath(settings_file);



	# Load settings
	modifiers = [];
	try:
		# Read file
		f = open(settings_file, "rb");
		settings_str = utf8_decode(f.read());
		f.close();

		# Parse
		m_data = parse_settings(settings_str, settings_vars);
		modifiers = m_data[0];
		m_errors = m_data[1];

		# Errors
		if (len(m_errors) > 0):
			# Display errors
			sys.stderr.write("Encountered {0:d} error{1:s} while parsing the settings file:\n".format(len(m_errors), ("" if len(m_errors) == 1 else "s")));
			for i in range(len(m_errors)):
				# Display error
				sys.stdout.write("Error on line {0:d}".format(m_errors[i]["line"] + 1));
				if (m_errors[i]["position"] >= 0):
					sys.stdout.write(" at position {0:d}".format(m_errors[i]["position"]));
				sys.stdout.write(":\n    {0:s}\n".format(str(m_errors[i]["message"])));

			# Return bad
			return -1;
		# Valid?
		if (len(modifiers) == 0):
			# Nothing
			sys.stderr.write("Nothing to be done; no modifiers\n");
			return 1;
	except IOError:
		# File error
		sys.stderr.write("Error opening settings file\n");
		return -1;
	debug = string_is_true(settings_vars["debug"]);



	# mkvmerge/mkvextract exe names
	exe_data = {
		"mkvmerge": {
			"filename": "mkvmerge",
			"checked": False
		},
		"mkvextract": {
			"filename": "mkvextract",
			"checked": False
		},
	};



	# Setup proper filenames and other info
	filenames_proper = [];
	for i in range(len(filenames)):
		# Setup
		filename = os.path.abspath(filenames[i]);
		is_mkv = os.path.splitext(filename)[1] in valid_mkv_extensions;
		filenames_proper.append({
			"filename": filename,
			"mkv": is_mkv
		});



	# Parse files
	for i in range(len(filenames)):
		# Setup
		sys.stdout.write("Processing {0:s}\n".format(filenames[i]));

		# Process
		r = main2(filenames_proper[i]["filename"], filenames_proper[i]["mkv"], modifiers, settings_vars, exe_data, debug, "    ", "    ");

		# Check return
		if (r != 0): return r;
		sys.stdout.write("\n");



	# Return okay
	return 0;



# Second part of main, which can be looped multiple times
def main2(filename, main_file_is_mkv, modifiers, settings_vars, exe_data, debug, stdout_prefix, stderr_prefix):
	# Filename splits
	old_filename_s1 = os.path.split(filename);
	old_filename_s2 = os.path.splitext(old_filename_s1[1]);



	# MKV or text check
	subtitle_extract_list = [];
	if (main_file_is_mkv):
		# Tracks
		while (True):
			f_info = get_info(exe_data["mkvmerge"]["filename"], filename, debug);
			if (f_info is None):
				if (update_exe_data(exe_data["mkvmerge"])): continue;
				sys.stderr.write("{0:s}An error occured while trying to execute {1:s}\n".format(stderr_prefix, mkvmerge_exe));
				return -1;
			break;

		tracks = f_info["tracks"];
		subtitle_id = 0;
		for i in range(len(tracks)):
			if (tracks[i]["type"] == "subtitles"):
				# Get target name
				track_ext = ".sub";
				if ("codec_id" in tracks[i]["extra"]):
					# Choose extension
					codec = tracks[i]["extra"]["codec_id"];
					if (codec == "S_TEXT/SSA"): track_ext = ".ssa";
					elif (codec == "S_TEXT/ASS"): track_ext = ".ass";
					elif (codec == "S_TEXT/UTF8"): track_ext = ".srt";

				track_target = old_filename_s2[0];
				track_target += ".subs-original-" + str(subtitle_id + 1);
				track_target = get_unique_filename(old_filename_s1[0], track_target, track_ext, 1, ".", "");

				track_target_new = old_filename_s2[0];
				track_target_new += ".subs-modified-" + str(subtitle_id + 1);
				track_target_new = get_unique_filename(old_filename_s1[0], track_target_new, track_ext, 1, ".", "");

				track_target_external = old_filename_s2[0];
				track_target_external += ".subs-" + str(subtitle_id + 1);
				track_target_external = get_unique_filename(old_filename_s1[0], track_target_external, track_ext, 1, ".", "");

				# Extract list
				language = "und";
				if ("language" in tracks[i]["extra"]): language = tracks[i]["extra"]["language"];
				track_title = "Subtitles";
				if ("track_name" in tracks[i]["extra"]): track_title = tracks[i]["extra"]["track_name"];
				subtitle_extract_list.append({
					"id": tracks[i]["id"],
					"filename": track_target,
					"filename_new": track_target_new,
					"filename_external": track_target_external,
					"language": language,
					"title": track_title
				});

				# Update id
				subtitle_id += 1;

		# Must be more than 0
		if (len(subtitle_extract_list) == 0):
			# Nothing
			sys.stderr.write("{0:s}Nothing to be done; no subtitles found\n".format(stderr_prefix));
			return 1;


		# Extract
		sys.stdout.write("{0:s}Extracting {1:d} subtitle track{2:s}...\n".format(stdout_prefix, len(subtitle_extract_list), ("" if (len(subtitle_extract_list) == 1) else "s")));
		while (True):
			okay = extract_tracks(exe_data["mkvextract"]["filename"], filename, subtitle_extract_list, debug);
			if (not okay):
				if (update_exe_data(exe_data["mkvextract"])): continue;
				sys.stderr.write("{0:s}An error occured while trying to execute {1:s}\n".format(stderr_prefix, mkvextract_exe));
				return -1;
			break;

	else:
		# Some sort of subtitle file, or plaintext
		track_ext = old_filename_s2[1];

		# Setup new names
		track_target_new = old_filename_s2[0];
		track_target_new += ".edited";
		track_target_new = get_unique_filename(old_filename_s1[0], track_target_new, track_ext, 1, ".", "");

		# Add to list
		subtitle_extract_list.append({
			"id": 0,
			"filename": filename,
			"filename_new": track_target_new,
			"filename_external": track_target_new,
			"language": "und",
			"title": "Subtitles"
		});



	# Modify subtitles
	for i in range(len(subtitle_extract_list)):
		sys.stdout.write("{0:s}Modifying subtitle track {1:d}...\n".format(stdout_prefix, i + 1));
		count = apply_modifiers_to_file(subtitle_extract_list[i]["filename"], subtitle_extract_list[i]["filename_new"], modifiers);
		sys.stdout.write("{0:s}    {1:d} modification{2:s} made\n".format(stdout_prefix, count, "" if count == 1 else "s"));



	# Remux the subtitles
	if (main_file_is_mkv):
		# Internal or external
		if (string_is_true(settings_vars["internal"])):

			# Generate filenames
			temp_filename = get_unique_filename(old_filename_s1[0], old_filename_s2[0] + ".script-edit", old_filename_s2[1], 1, ".", "");


			# Merge
			new_subtitles_tracks = [];
			for i in range(len(subtitle_extract_list)):
				# Modify title
				title_new = subtitle_extract_list[i]["title"]
				title_new = settings_vars["script"].replace("*", title_new);

				# Update list
				new_subtitles_tracks.append({
					"file": subtitle_extract_list[i]["filename_new"],
					"tracks": [{
						"id": 0,
						"title": title_new,
						"language": subtitle_extract_list[i]["language"]
					}]
				});
			# Keep original tracks?
			if (string_is_true(settings_vars["keep_original"])):
				original_tracks = [];
				for i in range(len(subtitle_extract_list)):
					original_tracks.append({
						"id": subtitle_extract_list[i]["id"],
						"title": None,
						"language": None
					});
				new_subtitles_tracks.append({
					"file": filename,
					"tracks": original_tracks
				});

			sys.stdout.write("{0:s}Remuxing with new subtitles...\n".format(stdout_prefix));
			while (True):
				okay = replace_subtitles(exe_data["mkvmerge"]["filename"], filename, temp_filename, new_subtitles_tracks, debug);
				if (not okay):
					if (update_exe_data(exe_data["mkvmerge"])): continue;
					sys.stderr.write("{0:s}An error occured while trying to execute {1:s}\n".format(stderr_prefix, mkvmerge_exe));
					return -1;
				break;

			# CRC
			new_filename_parts = parse_filename(old_filename_s2[0]);
			crc_new = None;
			if (string_is_true(settings_vars["crc"]) and filename_has_crc(new_filename_parts)):
				sys.stdout.write("{0:s}Recalculating CRC...\n".format(stdout_prefix));
				crc_new = get_file_crc(temp_filename);
				if (crc_new is not None):
					sys.stdout.write("{0:s}New CRC = {1:s}\n".format(stdout_prefix, "{0:08x}".format(crc_new).upper()));


			# Rename
			new_filename = change_filename(new_filename_parts, settings_vars["group"], crc_new);
			new_filename = get_unique_filename(old_filename_s1[0], new_filename, old_filename_s2[1], 1, ".", "");
			try:
				os.rename(temp_filename, new_filename);
			except:
				new_filename = temp_filename;


			# Remove temp
			sys.stdout.write("{0:s}Removing temporary files...\n".format(stdout_prefix));
			for i in range(len(subtitle_extract_list)):
				# Delete
				try:
					os.remove(subtitle_extract_list[i]["filename"]);
				except:
					pass;
				try:
					os.remove(subtitle_extract_list[i]["filename_new"]);
				except:
					pass;

		else:
			# Remove temp
			sys.stdout.write("{0:s}Removing temporary files...\n".format(stdout_prefix));
			for i in range(len(subtitle_extract_list)):
				# Delete
				try:
					os.remove(subtitle_extract_list[i]["filename"]);
				except:
					pass;



	# Done
	sys.stdout.write("{0:s}Complete\n".format(stdout_prefix));
	return 0;



# Execute
if (__name__ == "__main__"): sys.exit(main());

