import json
from collections import defaultdict

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://developer.mozilla.org"
URL_ELEMENTS = "https://developer.mozilla.org/en-US/docs/Web/HTML/Element"


def scrape():
    html_elements = defaultdict(lambda: {})
    _scrape_elements(html_elements)
    return html_elements


def _scrape_elements(html_elements: dict) -> None:
    # loads the "HTML elements reference" page
    request = requests.get(URL_ELEMENTS)
    soup = BeautifulSoup(request.content, "html.parser")

    html_elements["*"]["attributes"] = {}

    global_attributes_container = soup.find(id="sidebar-quicklinks").find('summary', string="Global attributes").find_parent()

    # loops through the listed global attributes in the sidebar
    for li in global_attributes_container.find_all('li'):
        is_experimental = bool(li.select_one(".icon.icon-experimental"))
        html_elements["*"]["attributes"][li.find('a').text] = {
            "experimental": is_experimental
        }

    html_elements_container = soup.find(id="sidebar-quicklinks").find('summary', string="HTML elements").find_parent()

    # loops through the listed html elements in the sidebar
    for li in html_elements_container.find_all('li'):
        # loads the element reference page
        request = requests.get(BASE_URL + li.find('a').get('href'))
        soup = BeautifulSoup(request.content, "html.parser")

        element_name = li.find('a').text.strip().lstrip("<").rstrip(">")
        is_deprecated = bool(soup.select_one('.section-content > .notecard.deprecated'))
        is_experimental = bool(soup.select_one('.section-content > .notecard.experimental'))

        html_elements[element_name]["deprecated"] = is_deprecated
        html_elements[element_name]["experimental"] = is_experimental
        html_elements[element_name]["attributes"] = {}

        supported_attributes_container = soup.find("section", attrs={"aria-labelledby": "attributes"})
        deprecated_attributes_container = soup.find("section", attrs={"aria-labelledby": "deprecated_attributes"})

        if supported_attributes_container:
            for attribute in supported_attributes_container.select(".section-content > dl > dt"):
                attribute_name = attribute.select_one('a code').text
                html_elements[element_name]["attributes"][attribute_name] = {
                    # sometimes, the supported and the deprecated attributes are in the same section, but the deprecated ones are marked with an icon instead
                    "deprecated": bool(attribute.select_one('.icon.icon-deprecated')),
                    "experimental": bool(attribute.select_one('.icon.icon-experimental'))
                }

        # in most pages, the deprecated attributes are grouped in a dedicated section
        if deprecated_attributes_container:
            for attribute in deprecated_attributes_container.select(".section-content > dl > dt"):
                attribute_name = attribute.select_one('a code').text
                html_elements[element_name]["attributes"][attribute_name] = {
                    "deprecated": True,
                    # AFAIK, there is no deprecated attribute that is also marked as "experimental"
                    "experimental": False
                }


def save_as_json(html_elements: dict) -> None:
    with open("html-elements.json", "w") as f:
        json.dump(html_elements, f, indent=4)


if __name__ == "__main__":
    elements = scrape()
    save_as_json(elements)
