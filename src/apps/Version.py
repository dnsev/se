#! /usr/bin/env python
import re, sys;

# Get version info
try:
	# Use version_info
	vi = list(sys.version_info[0 : 3]);
except:
	# Parse sys.version
	m = re.search(r"^([0-9]+\.?)+", sys.version);
	if (m):
		vi = m.group(0).split(".");
		for i in range(len(vi)): vi[i] = int(vi[i]);
	else:
		vi = [ 0 ];

# Argument pattern
pattern = re.compile(r"([0-9]+)(\+)?(-)?");
ret = 0;
i = 0;
for arg in sys.argv[1 : ]:
	m = pattern.match(arg.strip());
	if (m):
		# Version info
		v = 0;
		if (i < len(vi)): v = vi[i];
		n = int(m.group(1));
		can_be_less = (m.group(3) is not None);
		can_be_greater = (m.group(2) is not None);
		if (
			(v < n and not can_be_less) or
			(v > n and not can_be_greater)
		):
			# Version mismatch
			sys.stdout.write("Version mismatch: {0:s}".format(repr(vi)));
			ret = -1;
			break;

	# Next
	i += 1;

# Okay
sys.exit(ret);
