import json
import os
import copy
import re

from bs4 import BeautifulSoup, Tag, NavigableString, Comment, Doctype


def matching_tags(node_w, node_s):
    """
    Function checks if two nodes are matching tags.
    :param node_w: BeautifulSoup node of wrapper page
    :param node_s: BeautifulSoup node of wrapper page
    :return: boolean value indicating if the nodes are matching tags
    """
    return isinstance(node_w, Tag) and isinstance(node_s, Tag) and \
        (node_w.has_attr('id') and node_s.has_attr('id') and node_w['id'] == node_s['id'] or
         node_w.has_attr('class') and node_s.has_attr('class') and node_w['class'] == node_s['class'] or
         node_w.name == node_s.name and not node_w.has_attr('id') and not node_w.has_attr('id') or
         "roadrunner_optional" in node_w.attrs or "roadrunner_optional" in node_s.attrs)


def recurisve_match(node_w, node_s):
    """
    Function recursively matches nodes in the wrapper and sample.
    :param node_w: BeautifulSoup node of wrapper page
    :param node_s: BeautifulSoup node of wrapper page
    :return: boolean value indicating if the nodes are matching tags
    """
    if isinstance(node_w, NavigableString) and isinstance(node_s, NavigableString):
        return node_w == node_s or node_w == "#PCDATA"
    elif not matching_tags(node_w, node_s):
        return False
    elif matching_tags(node_w, node_s):
        matching = True
        for child_w, child_s in zip(node_w.children, node_s.children):
            matching = matching and recurisve_match(child_w, child_s)
        return matching


def discover_tag_iterators(node_list_w, node_list_s, i):
    """
    Function searches for iterators in the wrapper and sample and generalizes them to iterators in the wrapper.
    :param node_list_w: object with list of BeautifulSoup nodes of wrapper page
    :param node_list_s: object with list of BeautifulSoup nodes of sample page
    :param i: index of the current node in the wrapper
    :return index: index of the last node in the wrapper that was matched to the sample
    :return node_list_w: object with list of BeautifulSoup nodes of wrapper page
    """
    found_iterator = False
    # 1) Search for a possible iterator (square, i.e. <ul></ul> list): the + symbol

    # 2.1) Square location by Terminal-Tag Search

    if len(node_list_s) > i >= len(node_list_w):
        if len(node_list_w) == 0:
            return False, node_list_w
        # Take the last node in the wrapper as the terminal node
        terminal_node = node_list_w[-1]
    else:
        terminal_node = node_list_w[max(0, i - 1)]

    candidate_squares_wrapper = []
    candidate_squares_sample = []

    # 2.1.1) Explore candidate square on wrapper
    if i < len(node_list_w):
        initial_node = node_list_w[i]

        # Find the first node in the wrapper that matches the initial node
        for j in range(i - 2, 0, -1):
            if isinstance(node_list_w[j], Tag) and matching_tags(node_list_w[j], initial_node):
                candidate_squares_wrapper.append(node_list_w[j])
                break

    # 2.1.2) Explore candidate square on sample

    if i < len(node_list_s):
        initial_node = node_list_s[i]

        # Find the first node in the sample that matches the initial node
        for j in range(i - 1, 0, -1):
            if isinstance(node_list_s[j], Tag) and matching_tags(node_list_s[j], initial_node):
                candidate_squares_sample.append(node_list_s[j])
                break

    # 2.2) Square matching: try to match a square to a previous occurrence on either the sample or the wrapper
    matched_candidate = None
    for candidate_square in candidate_squares_wrapper:
        # Check if the square is a match
        if recurisve_match(terminal_node, candidate_square):
            found_iterator = True
            matched_candidate = terminal_node
            break

    if matched_candidate is not None:
        for candidate_square in candidate_squares_sample:
            # Check if the square is a match
            if recurisve_match(terminal_node, candidate_square):
                found_iterator = True
                matched_candidate = terminal_node
                break

    # 2.3) Wrapper generalization: find the longest square in wrapper and generalize it
    if found_iterator:
        # First mark all nodes in the square as iterators
        j = min(i, len(node_list_w) - 1)
        while j >= 0:
            if recurisve_match(node_list_w[j], matched_candidate):
                # Create a new object property to indicate that this node is optional
                node_list_w[j]["roadrunner_iterator"] = "()+"
            else:
                break
            j -= 1

        node_list_w = node_list_w[:j + 1]
        node_list_w.append(matched_candidate)
        matched_candidate["roadrunner_iterator"] = "()+"
        print("Found iterator: " + str(matched_candidate))

    return found_iterator, node_list_w


def discover_tag_optionals(node_list_w, node_list_s, i):
    """
    Function searches for optional tags in the wrapper and sample and generalizes them to optional tags in the wrapper.
    :param node_list_w: object with list of BeautifulSoup nodes of wrapper page
    :param node_list_s: object with list of BeautifulSoup nodes of sample page
    :param i: index of the current node in the wrapper
    :return index: index of the last node in the wrapper that was matched to the sample
    :return node_list_w: object with list of BeautifulSoup nodes of wrapper page
    """
    # 2) We look for optionals based on the missmatch: the ? symbol
    # 2.1) Optional pattern location by cross-search
    index = -1

    for j in range(i, max(len(node_list_w), len(node_list_s))):
        # Check if matching tag appeared
        if j < len(node_list_w) and j < len(node_list_s) and matching_tags(node_list_w[j], node_list_s[j]):
            index = j - i

            # Mark all nodes in wrapper between i and j as optional
            for k in range(i, j):
                if isinstance(node_list_w[k], Tag):
                    # Create a new object property to indicate that this node is optional
                    node_list_w[k]["roadrunner_optional"] = "()?"
                else:
                    # If the node was not a tag, we mark it as optional data
                    node_list_w[k] = "#OPTIONAL"
                # Add filler nodes to sample from wrapper
                node_list_s.insert(k, node_list_w[k])

            # Add optional nodes from sample
            for k in range(i, j):
                if isinstance(node_list_s[k], Tag):
                    # Create a new object property to indicate that this node is optional
                    node_list_s[k]["roadrunner_optional"] = "()?"
                else:
                    # If the node was not a tag, we mark it as optional data
                    node_list_s[k] = "#OPTIONAL"
                node_list_w.insert(k, node_list_s[k])
            return j, node_list_w

        # Search all previous wrapper tags that could match current sample tag
        elif j < len(node_list_s) and isinstance(node_list_s[j], Tag):
            tag_name_list = [el.name for el in node_list_w[i:min(j, len(node_list_w))] if isinstance(el, Tag)]
            if node_list_s[j].name in tag_name_list:
                # Find index of the matching tag in the wrapper
                index = tag_name_list.index(node_list_s[j].name)

                # Mark nodes in between matched and index as optional in wrapper
                for k in range(i, index):
                    if isinstance(node_list_w[k], Tag):
                        # Create a new object property to indicate that this node is optional
                        node_list_w[k]["roadrunner_optional"] = "()?"
                    else:
                        # If the node was not a tag, we mark it as optional data
                        node_list_w[k] = "#OPTIONAL"
                    # Add filler nodes to sample from wrapper
                    node_list_s.insert(k, node_list_w[k])

                # Add all sample nodes between i and i+index to wrapper
                for k in range(i, i + index + 1):
                    if isinstance(node_list_s[k], Tag):
                        # Create a new object property to indicate that this node is optional
                        node_list_s[k]["roadrunner_optional"] = "()?"
                    else:
                        # If the node was not a tag, we mark it as optional data
                        node_list_s[k] = "#OPTIONAL"
                    node_list_w.insert(k, node_list_s[k])

                index += i
                return index, node_list_w
        # Search all sample tags that could match current wrapper tag
        elif j < len(node_list_w) and isinstance(node_list_w[j], Tag):
            tag_name_list = [el.name for el in node_list_s[i:min(j, len(node_list_s))] if isinstance(el, Tag)]
            if node_list_w[j].name in tag_name_list:
                # Find index of the matching tag in the sample
                index = tag_name_list.index(node_list_w[j].name)

                # Add all optional nodes from sample between i and i+index to wrapper
                for k in range(i, i + index + 1):
                    if isinstance(node_list_s[k], Tag):
                        node_list_s[k]["roadrunner_optional"] = "()?"
                    else:
                        # If the node was not a tag, we mark it as optional data
                        node_list_s[k] = "#OPTIONAL"
                    node_list_w.insert(k, node_list_s[k])

                index += i
                return index, node_list_w

    # If no match was found in cross search, add all the remaining nodes from wrapper and sample as optional
    for k in range(i, len(node_list_w)):
        if isinstance(node_list_w[k], Tag):
            # Create a new object property to indicate that this node is optional
            node_list_w[k]["roadrunner_optional"] = "()?"
        else:
            # If the node was not a tag, we mark it as optional data
            node_list_w[k] = "#OPTIONAL"

    for k in range(i, len(node_list_s)):
        if isinstance(node_list_s[k], Tag):
            # Create a new object property to indicate that this node is optional
            node_list_s[k]["roadrunner_optional"] = "()?"
            node_list_w.append(node_list_s[k])
        else:
            # If the node was not a tag, we mark it as optional data
            node_list_s[k] = "#OPTIONAL"
        index += 1

    return index, node_list_w


def run_roadrunner(node_wrapper, node_sample):
    """
    Function creates a wrapper of AND-OR tree structure containing union-free regular expressions based on provided
    sample and wrapper page trees.
    ? for optional, + for iterator, ( ) for grouping and #PCDATA for any string
    :param node_wrapper: BeautifulSoup node of wrapper page
    :param node_sample: BeautifulSoup node of sample page
    """
    # 1) List of tokens called sample
    # 2) A wrapper of one union-free regular expression

    # The general approach works by taking the initial wrapper from page 1, and then
    # progressively refining trying to find a common regular expression between the
    # two pages.

    # Create temp node copies for each child
    children_w = [el for el in node_wrapper.children]
    children_s = [el for el in node_sample.children]
    if len(children_w) != len(children_s):
        # No children
        print("HOW")
    i = 0
    while i < len(children_w) and i < len(children_s):
        child_w = children_w[i]
        child_s = children_s[i]
        if matching_tags(child_w, child_s):
            # Tags are the same (node already in wrapper)
            # Recursively run roadrunner on children
            run_roadrunner(child_w, child_s)
        elif isinstance(child_w, NavigableString) and isinstance(child_s, NavigableString):
            # Both nodes are strings
            if child_w == child_s:
                # Strings are the same and already in wrapper
                pass
            else:
                # Strings are different replace with #PCDATA token
                children_w[i] = "#PCDATA"
        else:
            # Types are not aligned or tags are not the same

            # First try to find iterators
            found_iterator, new_children_w = discover_tag_iterators(children_w, children_s, i)

            # If no iterators were found, try to find optionals
            if not found_iterator:
                j, children_w = discover_tag_optionals(children_w, children_s, i)
                if j < 0:
                    break
                else:
                    i = j
                print("Found optionals")
            else:
                children_w = new_children_w
                print("Found iterators")
        i += 1

    # If there are remaining nodes in the sample, lets try to find iterators
    if i < len(children_s):
        found_iterator, new_children_w = discover_tag_iterators(children_w, children_s, i)
        if not found_iterator:
            # If iterators were not found, just add the remaining nodes to the wrapper as optionals
            for j in range(i, len(children_s)):
                if isinstance(children_s[j], Tag):
                    children_s[j]["roadrunner_optional"] = "()?"
                children_w.append(children_s[j])
        else:
            children_w = new_children_w

    # If there are remaining nodes in the wrapper, lets try to find iterators
    if i < len(children_w):
        found_iterator, new_children_w = discover_tag_iterators(children_w, children_s, i)
        if not found_iterator:
            # If iterators were not found, just add the remaining nodes to the wrapper as optionals
            for j in range(i, len(children_w)):
                if isinstance(children_w[j], Tag):
                    children_w[j]["roadrunner_optional"] = "()?"
                else:
                    # If the node was not a tag, we mark it as optional data
                    children_w[j] = "#OPTIONAL"
        else:
            children_w = new_children_w

    # We must update the children of the wrapper node
    node_wrapper.clear()
    for child in children_w:
        node_wrapper.append(child)


def filter_webpage(webpage):
    """
    Function filters a webpage of all unnecessary tags and attributes
    :param webpage: BeautifulSoup object of webpage
    :return: BeautifulSoup object of filtered webpage
    """
    # Remove all script tags
    for script in webpage.find_all("script"):
        script.decompose()

    # Remove all style tags
    for style in webpage.find_all("style"):
        style.decompose()

    # Remove all comments
    for comment in webpage.find_all(text=lambda text: isinstance(text, Comment)):
        comment.extract()

    # Remove all NavigableStrings with only whitespace
    for tag in webpage.find_all(text=lambda text: isinstance(text, NavigableString) and not text.strip()):
        tag.extract()

    # Remove all head tags
    for head in webpage.find_all("head"):
        head.decompose()

    # Remove all DOCTYPE tags
    for comment in webpage.find_all(text=lambda text: isinstance(text, Doctype)):
        comment.extract()

    # Remove all newline characters
    for tag in webpage.find_all(text=lambda text: isinstance(text, NavigableString)):
        tag.replace_with(tag.replace("\n", ""))

    # Remove all trailing and leading whitespace
    for tag in webpage.find_all(text=lambda text: isinstance(text, NavigableString)):
        tag.replace_with(tag.strip())

    # Remove all attributes except src and class and id
    for tag in webpage.find_all():
        class_attr = tag['class'] if 'class' in tag.attrs else None
        id_attr = tag['id'] if 'id' in tag.attrs else None
        tag.attrs.clear()
        if class_attr:
            tag['class'] = class_attr
        if id_attr:
            tag['id'] = id_attr

    return webpage


def create_site_wrapper(pages, site="rtvslo"):
    # First read all pages and convert to BeautifulSoup objects
    bs_objects = []
    for page in pages:
        try:
            bs_objects.append(BeautifulSoup(page, "lxml"))
        except Exception as e:
            print(f"Error while reading file {page}: {e}")
            exit(-1)

    # Create wrapper for all pages
    wrapper_root = filter_webpage(bs_objects[0])
    sample_root = filter_webpage(bs_objects[1])

    run_roadrunner(wrapper_root, sample_root)

    # Saving the wrappers into files inside results-extraction
    fname = f"..\\results\{site}-roadrunner.html"

    with open(fname, "w", encoding="utf-8") as f:
        f.write(wrapper_root.prettify())
