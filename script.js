// Title management
var default_title = "dnsev / se";
var page_list = {
	//"": null,
	"scripts": null,
	"documentation": null,
	"about": null,
	"changes": null,
};
var page_list_first_open_callback = {
	"use": function () {
		$(".UseImagePreviewSmall").each(function () {
			$(this).css("background-image", "url(" + ($(this).attr("data-preview-href")) + ")");
		});
	},
	"api": {
		"test": function () {
			launch_api();
		}
	},
};


// Date formatting
var date = (function () {

	var months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
	var months_short = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
	var days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
	var days_short = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
	var ordinal = ["st", "nd", "rd", "th", "th", "th", "th", "th", "th", "th", "th", "th", "th", "th", "th", "th", "th", "th", "th", "th", "st", "nd", "rd", "th", "th", "th", "th", "th", "th", "th", "st"];

	var format_value = function (date, format) {
		var s = "";
		if (format == 'd') { // Day of the month, 2 digits with leading zeros
			s += date.getDate();
			if (s.length < 2) s = "0" + s;
		}
		else if (format == 'j') { // Day of the month without leading zeros
			s += date.getDate();
		}
		else if (format == 'l') { // A full textual representation of the day of the week
			s += days[date.getDay()];
		}
		else if (format == 'D') { // A textual representation of a day, three letters
			s += days_short[date.getDay()];
		}
		else if (format == 'S') { // English ordinal suffix for the day of the month, 2 characters
			s +=ordinal[date.getDate() - 1];
		}
		else if (format == 'w') { // Numeric representation of the day of the week
			s += date.getDay();
		}
		else if (format == 'F') { // A full textual representation of a month, such as January or March
			s += months[date.getMonth()];
		}
		else if (format == 'M') { // A short textual representation of a month, three letters
			s += months_short[date.getMonth()];
		}
		else if (format == 'm') { // Numeric representation of a month, with leading zeros
			s += (date.getMonth() + 1);
			if (s.length < 2) s = "0" + s;
		}
		else if (format == 'n') { // Numeric representation of a month, without leading zeros
			s += (date.getMonth() + 1);
		}
		else if (format == 'y') { // Year, 2 digits
			s += date.getFullYear().toString().substr(2);
		}
		else if (format == 'Y') { // A full numeric representation of a year, 4 digits
			s += date.getFullYear();
		}
		else if (format == 'a') { // Lowercase Ante meridiem and Post meridiem
			s += (date.getHours() >= 11 && date.getHours() <= 22 ? "pm" : "am");
		}
		else if (format == 'A') { // Uppercase Ante meridiem and Post meridiem
			s += (date.getHours() >= 11 && date.getHours() <= 22 ? "PM" : "AM");
		}
		else if (format == 'g') { // 12-hour format of an hour without leading zeros
			s += (date.getHours() % 12) + 1;
		}
		else if (format == 'h') { // 12-hour format of an hour with leading zeros
			s += (date.getHours() % 12) + 1;
			if (s.length < 2) s = "0" + s;
		}
		else if (format == 'G') { // 24-hour format of an hour without leading zeros
			s += date.getHours();
		}
		else if (format == 'H') { // 24-hour format of an hour with leading zeros
			s += date.getHours();
			if (s.length < 2) s = "0" + s;
		}
		else if (format == 'i') { // Minutes with leading zeros
			s += date.getMinutes();
			if (s.length < 2) s = "0" + s;
		}
		else if (format == 's') { // Seconds with leading zeros
			s += date.getSeconds();
			if (s.length < 2) s = "0" + s;
		}
		else if (format == 'u') { // Microseconds
			s += date.getMilliseconds();
		}
		else { // Unknown
			s += format;
		}
		return s;
	}

	return {

		format: function (timestamp, format) {
			// Based on: http://php.net/manual/en/function.date.php
			var date = new Date(timestamp);

			return format.replace(/(\\*)([a-zA-Z])/g, function (match, esc, fmt) {
				if (esc.length > 0) {
					if ((esc.length % 2) == 1) {
						// Escaped
						return esc.substr(1, (esc.length - 1) / 2) + fmt;
					}
					// Remove slashes
					return esc.substr(0, esc.length / 2) + format_value(date, fmt);
				}
				return format_value(date, fmt);
			});
		}

	};

})();


// Basic functions
function is_chrome() {
	return ((navigator.userAgent + "").indexOf(" Chrome/") >= 0);
}
function is_firefox() {
	var ua = navigator.userAgent + "";
	return (ua.indexOf("Mozilla/") >= 0 && ua.indexOf("MSIE") < 0);
}

function text_to_html(str) {
	return str.replace(/&/g, "&amp;")
		.replace(/>/g, "&gt;")
		.replace(/</g, "&lt;")
		.replace(/"/g, "&quot;");
}

function change_style_display(class_names, display_prefix, on) {
	on = on ? 1 : 0;
	$("." + class_names[on]).removeClass(display_prefix + "DisplayOff").addClass(display_prefix + "DisplayOn");
	$("." + class_names[1 - on]).removeClass(display_prefix + "DisplayOn").addClass(display_prefix + "DisplayOff");
}
function change_browser_display(show_all) {
	if (!show_all && is_chrome()) {
		$(".SpecificBrowser").removeClass("BrowserDisplayOff").addClass("BrowserDisplayOn");
		$(".Firefox").removeClass("BrowserDisplayOn").addClass("BrowserDisplayOff");
		$(".UniversalBrowser").removeClass("BrowserDisplayOn").addClass("BrowserDisplayOff");
		$(".Chrome").removeClass("BrowserDisplayOff").addClass("BrowserDisplayOn");
	}
	else if (!show_all && is_firefox()) {
		$(".SpecificBrowser").removeClass("BrowserDisplayOff").addClass("BrowserDisplayOn");
		$(".Chrome").removeClass("BrowserDisplayOn").addClass("BrowserDisplayOff");
		$(".UniversalBrowser").removeClass("BrowserDisplayOn").addClass("BrowserDisplayOff");
		$(".Firefox").removeClass("BrowserDisplayOff").addClass("BrowserDisplayOn");
	}
	else {
		$(".Firefox").removeClass("BrowserDisplayOff").addClass("BrowserDisplayOn");
		$(".Chrome").removeClass("BrowserDisplayOff").addClass("BrowserDisplayOn");
		$(".SpecificBrowser").removeClass("BrowserDisplayOn").addClass("BrowserDisplayOff");
		$(".UniversalBrowser").removeClass("BrowserDisplayOff").addClass("BrowserDisplayOn");
	}
}
var elem = function (tag) {
	var e = document.createElement(tag);
	if (arguments.length > 1) e.className = arguments[1];
	return $(e);
};

// Custom links
var internal_link_class_list = {
};
function activate_internal_link(link) {
	// Check if it has a class
	var cl = link.attr("link_class");
	if (!cl) return true;

	// What to do
	var fcn = internal_link_class_list[cl];
	if (!fcn) return true;

	// Run the function
	return fcn(link);
}

// Window url hash management
function WindowHash() {
	this.hash = "";
	this.page = "";
	this.vars = {};
	this.history_mode = 0;

	this.history = [];
	this.history_index = -1;
};
WindowHash.prototype = {
	constructor: WindowHash,
	on_change: function (event) {
		if (this.hash == window.location.hash) return;

		// Get the new hash
		this.hash = window.location.hash;
		if (this.hash.length > 0) this.hash = this.hash.substr(1);

		// Get the page
		var h = this.hash.split("?");
		this.page = h[0];

		// Get any variables
		this.vars = this.parse_vars(h.splice(1, h.length - 1).join("?"));

		// History update
		if (this.history_mode == 0) {
			if (this.history_index < this.history.length - 1) {
				this.history.splice(this.history_index, this.history.length - 1 - this.history_index);
			}
			this.history.push([this.hash , this.page , this.vars]);
			++this.history_index;
		}
		else {
			this.history_index += this.history_mode;
			alert(this.history[this.history_index][0] + "\n" + this.hash);
		}
	},
	goto_page: function (page, vars) {
		page = page || "";

		var i = 0;
		for (var a = 1; a < arguments.length; ++a) {
			for (var v in arguments[a]) {
				page += (i == 0 ? "?" : "&") + v + (arguments[a][v] === null ? "" : "=" + arguments[a][v]);
				++i;
			}
		}

		window.location.hash = page;
	},
	has_previous: function () {
		return (this.history_index > 0);
	},
	goto_previous: function () {
		if (this.history_index > 0) {
			this.history_mode = -1;
			window.location.hash = this.history[this.history_index - 1][0];
			this.on_change();
			this.history_mode = 0;

			return true;
		}
		return false;
	},
	has_next: function () {
		return (this.history_index < this.history.length - 1);
	},
	goto_next: function () {
		if (this.history_index < this.history.length - 1) {
			this.history_mode = 1;
			window.location.hash = this.history[this.history_index + 1][0];
			this.on_change();
			this.history_mode = 0;

			return true;
		}
		return false;
	},
	parse_vars: function (str) {
		var vars = {};
		var h = str.split("&");
		for (var i = 0; i < h.length; ++i) {
			if (h[i].length == 0) continue;
			var p = h[i].split("=");
			vars[p[0]] = (p.length == 1) ? null : p.splice(1, p.length - 1).join("=");
		}

		return vars;
	},
	modify_href: function (href) {
		if (href == ".") href = this.page;
		else if (href == "..") {
			href = this.page.split("/");
			href = href.slice(0, href.length - 1).join("/");
		}
		return href;
		// TODO
	}
};
var window_hash = new WindowHash();

// Pages
function maintain_vars(vars, maintain) {
	var v = {};

	for (var k in vars) {
		for (var i = 0; i < maintain.length; ++i) {
			if (maintain[i] == k) {
				v[k] = vars[k];
				break;
			}
		}
	}

	return v;
}
function remove_vars(vars, remove) {
	var v = {};

	for (var k in vars) {
		for (var i = 0; i < remove.length; ++i) {
			if (remove[i] == k) {
				k = null;
				break;
			}
		}
		if (k !== null) v[k] = vars[k];
	}

	return v;
}
function PageBrowser() {

}
PageBrowser.prototype = {
	constructor: PageBrowser,
	open: function (page, vars, refresh) {
		// Which page
		var title = "";
		var p = page.split("/");
		var s = page_list;
		var nav_page = page;
		for (var i = 0; i < p.length; ++i) {
			if (s !== null && p[i] in s) {
				s = s[p[i]];
				title += (title.length == 0 ? "" : " / ") + p[i];
				if (i == 0) nav_page = p[i];
			}
			else {
				title = "SubEdit";
				nav_page = page = "";
			}
		}
		// Callbacks
		s = page_list_first_open_callback;
		for (var i = 0; i < p.length; ++i) {
			if (s !== null && p[i] in s) {
				if (i == p.length - 1) {
					if (s[p[i]] != null && typeof(s[p[i]]) === "function") {
						s[p[i]]();
						s[p[i]] = null;
					}
					break;
				}
				s = s[p[i]];
			}
			else {
				break;
			}
		}

		$(".Content").removeClass("ContentActive");
		$(".NavigationLink").removeClass("NavigationLinkCurrent");
		$("#content_" + page.replace(/\W/g, "_")).addClass("ContentActive");
		$("#navigation_" + nav_page).addClass("NavigationLinkCurrent");

		$("title").html(default_title + (title.length == 0 ? "" : " / " + title));
		change_browser_display(true);

		$(".PageVariableDisplay").each(function () {
			$(this)
			.removeClass("PageVariableDisplayOn PageVariableDisplayOff")
			.addClass("PageVariableDisplay" + (($(this).attr("data-pvar") in vars) ? "Off" : "On"));
		});
		$(".PageVariableDisplayInv").each(function () {
			$(this)
			.removeClass("PageVariableDisplayOn PageVariableDisplayOff")
			.addClass("PageVariableDisplay" + (($(this).attr("data-pvar") in vars) ? "On" : "Off"));
		});

		image_preview_close();

		// Scroll
		update_page_actions();
	}
};
var page_browser = new PageBrowser();
function maintain(extra) {
	var s_type = typeof("");
	var a_type = typeof([]);

	var r = page_vars_maintain;
	for (var i = 0; i < arguments.length; ++i) {
		if (typeof(arguments[i]) == s_type) r = r.concat(arguments[i]).split(",");
		else if (typeof(arguments[i]) == a_type) r = r.concat(arguments[i]);
	}

	return r;
}
var page_vars_maintain = [];
function update_page_actions() {
	var vars = window_hash.vars;

	var scrolled = false;
	if ("scroll" in vars) {
		var scroll_to = $("[data-multi-id=" + vars["scroll"].replace(/\W/g, "\\$&") + "]:visible");
		if (scroll_to.length > 0) {
			try {
				$(document).scrollTop(scroll_to.offset().top);
				scrolled = true;
			}
			catch (e) {}
		}
	}

	$(".Highlighted").removeClass("Highlighted");
	if ("highlight" in vars) {
		var hl = $("[data-multi-id=" + vars["highlight"].replace(/\W/g, "\\$&") + "]:visible");
		if (hl.length > 0) {
			hl.addClass("Highlighted");
		}
	}

	if ("activate" in vars) {
		var activate = $("[data-multi-id=" + vars["activate"].replace(/\W/g, "\\$&") + "]:visible");
		if (activate.length > 0) {
			$(activate[0]).trigger("click");
		}
	}
}

// Acquire changelog
var acquire_changelog = (function () {

	var checked = false;

	return function () {
		if (checked) return;

		$.ajax({
			type: "GET",
			url: "https://api.github.com/repos/dnsev/se/commits",
			dataType: "json",
			cache: "true",
			success: function (data, status, jq_xhr) {
				checked = true;

				var changelog = parse_changelog(data);
				display_changelog(changelog);
			},
			error: function (jq_xhr, status) {
				checked = true;

				$(".changelog")
				.addClass("error")
					.find(".changelog_status")
					.attr("data-error-message", "Status: " + jq_xhr.status + " / " + status);
			}
		});
	};

})();
var title_is_relevant = function (title) {
	return /[0-9\.]/.test(title);
};
var parse_changelog = function (gcl) {
	var changelog = [];

	for (var i = 0; i < gcl.length; ++i) {
		var title = gcl[i].commit.message.replace(/\s*\n\s*(0|[^0])*$/, "");

		if (title_is_relevant(title)) {
			var entry = {
				sha: gcl[i].sha,
				title: title,
				comment: gcl[i].commit.message.replace(/^[^\r\n]*\r?\n?\r?\n?/, ""),
				timestamp: 0,
			};

			var date = /^([0-9]+)-([0-9]+)-([0-9]+)T([0-9]+):([0-9]+):([0-9]+)Z$/.exec(gcl[i].commit.committer.date);
			if (date) {
				entry.timestamp = (new Date(
					parseInt(date[1]),
					parseInt(date[2]) - 1,
					parseInt(date[3]),
					parseInt(date[4]),
					parseInt(date[5]),
					parseInt(date[6])
				)).getTime();
			}

			changelog.push(entry);
		}
	}

	return changelog;
};
var display_changelog = function (changelog) {
	var timezone_offset = -(new Date()).getTimezoneOffset() * 60 * 1000;

	var container = $(".changelog");
	container.html("").addClass("loaded");

	for (var i = 0; i < changelog.length; ++i) {
		var item = elem("div", "changelog_item");
		var title = elem("div", "changelog_item_title");
		var content = elem("ul", "changelog_item_content");

		// Title
		title.append(
			elem("a", "changelog_item_title_link")
			.text(changelog[i].title)
			.attr("target", "_blank")
			.attr("href", "https://github.com/dnsev/se/commit/" + changelog[i].sha)
		)
		.append(
			elem("span", "changelog_item_title_date")
			.text(date.format(changelog[i].timestamp + timezone_offset, "F jS, Y @ G:i"))
		);

		// Changes list
		var changes = changelog[i].comment.split("\n");
		// Fix back into a single line if necessary (lines must begin with "- " to be correct)
		for (var j = 0; j < changes.length; ++j) {
			if (!/^-\s/.test(changes[j]) && j > 0) {
				changes[j - 1] = changes[j - 1].replace(/\s+$/g, "") + " " + changes[j].replace(/^\s+/g, "");
				changes.splice(j, 1);
				--j;
			}
		}
		for (var j = 0; j < changes.length; ++j) {
			changes[j] = changes[j].replace(/^-\s*|\s+$/g, "");
		}
		// Add change
		for (var j = 0; j < changes.length; ++j) {
			content.append(
				elem("li", "changelog_item_change")
				.text(changes[j])
			);
		}

		// Add
		container.append(item.append(title).append(content));
	}

	// Set version
	if (changelog.length > 0) {
		$(".Version").html(changelog[0].title);
	}
};

// Image previewing
function image_preview(obj) {
	// Only open if necessary
	if ($(".ImagePreviewBoxInner2").length > 0) {
		return;
	}

	var descr = (obj.next().length > 0 ? (obj.next().hasClass && obj.next().hasClass("ImageDescription") ? obj.next().html() : "") : "");
	var descr_container, img_append, offset, offset2;

	// Create new
	$("body").append(
		(offset = $(document.createElement("div")))
		.addClass("ImagePreviewBoxInner2")
		.append(
			(offset2 = $(document.createElement("div")))
			.append(
				(img_append = $(document.createElement("a")))
				.addClass("ImagePreviewImageContainer")
				.attr("href", obj.attr("href"))
				.attr("target", "_blank")
				.on("click", function (event) {
					return false;
				})
			)
			.append(
				(descr_container = $(document.createElement("div")))
				.addClass("ImagePreviewDescriptionContainer")
				.html(descr)
			)
		)
		.on("click", {}, function (event) {
			if (event.which == 1) {
				return false;
			}
			return true;
		})
		.css({"left": "0", "top": "0", "opacity": "0"})
	);

	// Click to close
	$(".ImagePreviewOverlay")
	.on("click", {href: "#" + window_hash.page}, function (event) {
		if (event.which == 1) {
			image_preview_close();
			// Change URL
			window_hash.goto_page(
				event.data.href,
				remove_vars(window_hash.vars, ["activate", "scroll"])
			);
			return false;
		}
		return true;
	});

	// Image
	img_append.append(
		$(document.createElement("img"))
		.attr("src", obj.attr("href"))
		.on("load", {}, function (event) {
			// Image loaded; open
			descr_container.css({
				"max-width": Math.max(640, this.width) + "px"
			});
			var w = descr_container.outerWidth();
			descr_container.css({
				"width": w,
				"max-width": ""
			});
			offset.css({
				"left": (-offset.outerWidth() / 2) + "px",
				"top": (-offset.outerHeight() / 2) + "px",
			});
			$(".ImagePreviewOverlayInner").html(
				$(document.createElement("div"))
				.addClass("ImagePreviewBox")
				.append(
					$(document.createElement("div"))
					.addClass("ImagePreviewBoxInner1")
					.append(
						offset
						.css("opacity", "")
					)
				)
			);
			$(".ImagePreviewOverlay").css("display", "block");
		})
	);
}
function image_preview_close() {
	$(".ImagePreviewBoxInner2").remove();
	$(".ImagePreviewOverlay")
	.off("click")
	.css("display", "");
}

// Entry
$(document).ready(function () {
	// Events
	$(".Link").on("click", {}, function (event) {
		if (event.which == 1) {
			event.stopPropagation();
			return true;
		}
		return true;
	});
	$(".NavigationLink:not(.NavigationLinkDirect)").on("click", {}, function (event) {
		if (event.which == 1) {
			window_hash.goto_page(
				$(this).attr("href")[0] == "#" ? $(this).attr("href").substr(1) : $(this).attr("id").substr("navigation_".length),
				maintain_vars(window_hash.vars, maintain($(this).attr("maintain")))
			);
			return false;
		}
		return true;
	});
	$(".ImageLink").on("click", {}, function (event) {
		if (event.which == 1 || event.which === undefined) {
			var href = $(this).attr("href_update").substr(1).split("?");
			window_hash.goto_page(
				window_hash.modify_href(href[0]),
				maintain_vars(window_hash.vars, maintain($(this).attr("maintain"))),
				(href[1] ? window_hash.parse_vars(href[1]) : undefined)
			);

			image_preview($(this));
			return false;
		}
		return true;
	});
	$(".InternalLink").on("click", {}, function (event) {
		if ((event.which == 1 || event.which === undefined) && $(this).attr("href")[0] == "#") {
			var href = $(this).attr("href").substr(1).split("?");
			window_hash.goto_page(
				window_hash.modify_href(href[0]),
				maintain_vars(window_hash.vars, maintain($(this).attr("maintain"))),
				(href[1] ? window_hash.parse_vars(href[1]) : undefined)
			);
			return false;
		}
		return true;
	});
	$(".Version").on("click", {}, function (event) {
		if ((event.which == 1 || event.which === undefined)) {
			var href = ("#changes").substr(1).split("?");
			window_hash.goto_page(
				window_hash.modify_href(href[0]),
				maintain_vars(window_hash.vars, maintain($(this).attr("maintain"))),
				(href[1] ? window_hash.parse_vars(href[1]) : undefined)
			);
			return false;
		}
		return true;
	});

	$(".doc-navigation-link").each(function () {
		var target = $(this).attr("href").replace(/^#!?/g, "");
		target = "#documentation?scroll=" + target;

		$(this).attr("href", target);
	});

	// Page display
	var hashchange = function (event) {
		window_hash.on_change(event);
		page_browser.open(window_hash.page, window_hash.vars, event===null);
	};
	$(window).on("hashchange", {}, hashchange);
	hashchange(null);

	// Get the changelog
	acquire_changelog();
});


