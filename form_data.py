import re

browsers = {
    "combi_win_10_chrome": {
        "os": "Windows",
        "os_version": "10",
        "browser": "chrome",
        "device": None,
        "browser_version": "71.0",
        "real_mobile": None
    },
    "combi_win_10_ff": {
        "os": "Windows",
        "os_version": "10",
        "browser": "firefox",
        "device": None,
        "browser_version": "63.0",
        "real_mobile": None
    },

    "combi_win_10_ie11": {
        "os": "Windows",
        "os_version": "10",
        "browser": "ie",
        "browser_version": "11.0"
    },

    "combi_win_10_edge": {
        "os": "Windows",
        "os_version": "10",
        "browser": "edge",
        "browser_version": "18.0"
    },

    "combi_win_8_chrome": {
        "os": "Windows",
        "os_version": "8.1",
        "browser": "chrome",
        "device": None,
        "browser_version": "71.0",
        "real_mobile": None
    },
    "combi_win_8_ff": {
        "os": "Windows",
        "os_version": "8.1",
        "browser": "firefox",
        "device": None,
        "browser_version": "63.0",
        "real_mobile": None
    },
    "combi_win_8_ie11": {
        "os": "Windows",
        "os_version": "8.1",
        "browser": "ie",
        "device": None,
        "browser_version": "11.0",
        "real_mobile": None
    },

    "combi_mojave_chrome": {
        "os": "OS X",
        "os_version": "Mojave",
        "browser": "chrome",
        "device": None,
        "browser_version": "71.0",
        "real_mobile": None
    },

    "combi_mojave_ff": {
        "os": "OS X",
        "os_version": "Mojave",
        "browser": "firefox",
        "device": None,
        "browser_version": "63.0",
        "real_mobile": None
    },
    "combi_mojave_safari": {
        "os": "OS X",
        "os_version": "Mojave",
        "browser": "safari",
        "device": None,
        "browser_version": "12.0",
        "real_mobile": None
    },

    "combi_high_sierra_chrome": {
        "os": "OS X",
        "os_version": "High Sierra",
        "browser": "chrome",
        "device": None,
        "browser_version": "71.0",
        "real_mobile": None
    },

    "combi_high_sierra_ff": {
        "os": "OS X",
        "os_version": "High Sierra",
        "browser": "firefox",
        "device": None,
        "browser_version": "63.0",
        "real_mobile": None
    },
    "combi_high_sierra_safari": {
        "os": "OS X",
        "os_version": "High Sierra",
        "browser": "safari",
        "device": None,
        "browser_version": "11.1",
        "real_mobile": None
    },

    "combi_catalina_chrome": {
        "os": "OS X",
        "os_version": "Catalina",
        "browser": "chrome",
        "device": None,
        "browser_version": "71.0",
        "real_mobile": None
    },
    "combi_catalina_safari": {
        "os": "OS X",
        "os_version": "Catalina",
        "browser": "safari",
        "device": None,
        "browser_version": "13.0",
        "real_mobile": None
    },

    "combi_ios_12_ipad_11": {
        "os": "ios",
        "os_version": "12",
        "browser": "Mobile Safari",
        "device": "iPad Pro 11 2018",
        "browser_version": None,
        "real_mobile": True
    },
    "combi_ios_12_ipad_12": {
        "os": "ios",
        "os_version": "12",
        "browser": "Mobile Safari",
        "device": "iPad Pro 12.9 2018",
        "browser_version": None,
        "real_mobile": True
    },
    "combi_ios_11_ipad_12": {
        "os": "ios",
        "os_version": "11",
        "browser": "Mobile Safari",
        "device": "iPad Pro 12.9 2017",
        "browser_version": None,
        "real_mobile": True
    },

    "combi_ios_11_ipad_9": {
        "os": "ios",
        "os_version": "11",
        "browser": "Mobile Safari",
        "device": "iPad Pro 9.7 2016",
        "browser_version": None,
        "real_mobile": True
    },
    "combi_ios_11_ipad_6th": {
        "os": "ios",
        "os_version": "11",
        "browser": "Mobile Safari",
        "device": "iPad 6th",
        "browser_version": None,
        "real_mobile": True
    },
    "combi_galaxy_note_9": {
        "os": "android",
        "os_version": "8.1",
        "browser": "Android Browser",
        "device": "Samsung Galaxy Note 9",
        "browser_version": None,
        "real_mobile": True
    },

    "combi_ios_12_iphone_6s": {
        "os": "ios",
        "os_version": "12",
        "browser": "Mobile Safari",
        "device": "iPhone 6S",
        "browser_version": None,
        "real_mobile": True
    },
    "combi_ios_12_iphone_8": {
        "os": "ios",
        "os_version": "12",
        "browser": "Mobile Safari",
        "device": "iPhone 8",
        "browser_version": None,
        "real_mobile": True
    },
    "combi_ios_12_iphone_xr": {
        "os": "ios",
        "os_version": "12",
        "browser": "Mobile Safari",
        "device": "iPhone XR",
        "browser_version": None,
        "real_mobile": True
    },
    "combi_ios_12_iphone_xs": {
        "os": "ios",
        "os_version": "12",
        "browser": "Mobile Safari",
        "device": "iPhone XS",
        "browser_version": None,
        "real_mobile": True
    },
    "combi_ios_11_iphone_se": {
        "os": "ios",
        "os_version": "11",
        "browser": "Mobile Safari",
        "device": "iPhone SE",
        "browser_version": None,
        "real_mobile": True
    },
    "combi_ios_11_iphone_x": {
        "os": "ios",
        "os_version": "11",
        "browser": "Mobile Safari",
        "device": "iPhone X",
        "browser_version": None,
        "real_mobile": True
    },
    "combi_galaxy_s9": {
        "os": "android",
        "os_version": "8.0",
        "browser": "Android Browser",
        "device": "Samsung Galaxy S9",
        "browser_version": None,
        "real_mobile": True
    },
    "combi_galaxy_s10": {
        "os": "android",
        "os_version": "9.0",
        "browser": "Android Browser",
        "device": "Samsung Galaxy S10",
        "browser_version": None,
        "real_mobile": True
    }

}


def get_browser_list(form_data):
    """ return a list of browsers based on provided form data"""

    browser_list = []
    for key in form_data:
        if key in browsers:
            browser_list.append(browsers[key])

    return browser_list


def clean_web_list(form_websites):
    """ splits on whitespace character or comma, then removes any left over white space items from the list"""
    form_websites = re.split(r"\s+|,(\s)+", form_websites)  # split on whitespace OR whitespace then comma [" ", " ,"] DO NOT SPLIT ON comma only  [","]
    cleaned = []
    for item in form_websites:
        if item and re.match(r"\S", item):  # ignore strings that start with a non-whitespace character
            cleaned.append(item)
    return cleaned
