"""
Contains everything (should honestly be separated across
several python files but I got frustrated with module not found
and just moved on xd)
"""

from aqt import mw, gui_hooks
from aqt.utils import showInfo, qconnect
from aqt.qt import *
import json
import os

# Makes sure that working directory is the add-on folder
abs_path = os.path.abspath(__file__)
path_of_this_file = os.path.dirname(abs_path)
os.chdir(path_of_this_file)

def open_manual_population(editor):
    """
    Opens the menu to cycle through population options for individual fields.
    """    


def perform_auto_cycle(editor):
    """
    Automatically populates fields from notetype, in order determined by config.json.
    """

    search_phrase = get_search_phrase(editor)

    if search_phrase == "":
        return

    # entire loop, for each field, will search source deck for 1 card with phrase,
    # and if it exists, return info from corresponding source field.
    # if not found, do another cycle.
    # if more cycles called like this than deck number, end function call and
    # display info accordingly

    # if manual cycle was used right before, and user wants to do auto cycle
    # just reset all field cycles back to 0th deck
    if last_cycle_was_manual:
        for i in field_cycles:
            field_cycles[i] = 0

    info_found = False
    num_loops = 0
    
    while ((not info_found) and num_loops < num_decks):
        source_card = search_for_card(field_cycles[0], search_phrase)
        save = field_cycles[0]
        cycle_all_fields()
        num_loops += 1

        if source_card != 0:
            info_found = True

    if (not info_found) and num_loops == num_decks:
        showInfo("Card not found")
        return

    for i in range(num_fields):
        put_info_into_editor(editor, source_card, i, save)


def put_info_into_editor(editor, source_card, field_index, deck_index):
    """
    Given a card object and field name, get the information from
    that card's field and paste it into the editor accordingly.
    """
    source_field = user_config["source_fields"][deck_index][field_index]
    print("\nSOURCE FIELD:")
    print(source_field)

    if not isinstance(source_field, str):  # if user put a 0 for a field,
        return                           # ignore field

    source_note = source_card.note()
    card_content = source_note[source_field]


    destination_field = user_config["destination_fields"][field_index]
    current_note = editor.note
    current_note[destination_field] = card_content

     # Mark the note as modified and refresh the editor
    editor.loadNote()  # Refresh the editor to display the updated content

def get_search_phrase(editor):
    """
    Obtains what user has typed into designated search field
    """

    search_phrase = editor.note.items()[0][1]
    print("\nSEARCH PHRASE: (by default, console cannot print japanese text)")
    print(search_phrase)

    return search_phrase


def search_for_card(index, search_phrase):
    """
    Returns card object from given deck with a phrase in
    field corresponding to destination deck's search field.
    """

    deck = mw.col.decks.by_name(user_config["source_decks"][index])
    card_ids = (mw.col.find_cards(search_phrase))

    card_objects = []
    for i in card_ids:
        card_objects.append(mw.col.get_card(i))
    

    for card_object in card_objects:
        source_note = mw.col.get_note(card_object.nid)
        if ( # need to add another condition: is search_phrase in correct field?
            card_is_in_deck(card_object, deck["id"])
            and phrase_in_right_field(card_object, search_phrase, index)
            and notetype_matches(card_object, user_config["source_notetypes"][index])
            and cardtype_matches(card_object, user_config["source_cardtypes"][index])
            and custom_matches(card_object, user_config["custom_type_fields"][index], user_config["custom_type_field_content"][index])
            ):
            return card_object
    
    # this happens if there isn't a single matching card
    return 0


def phrase_in_right_field(card_object, search_phrase, index):
    note_object = mw.col.get_note(card_object.nid)

    

    try:
        if search_phrase == note_object[user_config["fields_to_search_in"][index]]:
            return True
        else:
            return False
    except:
        print("exception called !!!! returning false")
        return False
        

def card_is_in_deck(card, deck_id):
    """
    Returns true if card is within deck corresponding to id of deck
    and notetype, false otherwise
    """
    if card.did == deck_id:
        return True
    else:
        return False


def notetype_matches(card, notetype_name):
    """
    Returns true if card's notetype matches the notetype specified in notetype_name string
    """
    if card.note_type()["name"] == notetype_name:
        return True
    else:
        return False


def cardtype_matches(card, cardtype_name):
    """
    Returns true if card's cardtype matches the cardtype specified in cardtype_name string
    """
    if not isinstance(cardtype_name, str):
        return True
    note_type = card.note_type()
    template_index = card.ord

    if note_type['tmpls'][template_index]['name'] == cardtype_name:
        return True
    else:
        return False
    
def custom_matches(card, field_name, intended_content):

    if (not isinstance(field_name, str)) or (not isinstance(intended_content, str)):
        return True

    note_object = mw.col.get_note(card.nid)
    content = note_object[field_name]

    if content == intended_content:
        return True
    else:
        return False



def cycle_all_fields():
    """
    Increments every integer in field_cycles.
    """
    for i in range(num_fields):
        cycle_field(i)


def cycle_field(field_index):
    """
    Increments a field's number in field_cycles that tracks which
    decks it has cycled through, or goes back to start.
    """

    # if before the last cycle, increment up
    if field_cycles[field_index] < max_index:
        field_cycles[field_index] += 1

    #if at last cycle, reset to cycle 0
    else:
        field_cycles[field_index] = 0


def get_note_type_id(deck_id, notetype_name):
    """ Return a list of the IDs of note types used
        in a deck.
    """

    card_ids = mw.col.decks.cids(deck_id)
    note_type_ids = []
    for cid in card_ids:
        note_type_ids.append(mw.col.get_card(cid).note_type()['id'])
    
    for ntid in note_type_ids:
        if mw.col.get_aux_notetype_config(ntid) == notetype_name:
            return ntid


def add_editor_buttons(buttons, editor):
    """
    Add population buttons to editor menu.
    """

    # get file paths for icons
    icon_manual_path = os.path.join(path_of_this_file, "icon_manual.png")
    icon_auto_path = os.path.join(path_of_this_file, "icon_auto.png")

    # editor button for manually choose data from configured notetypes to populate
    manual_button = editor.addButton(
        icon = icon_manual_path,
        cmd = "manualpopulate",
        func = open_manual_population,
        tip = "Open menu to pick and choose from configured notetypes to populate each field"
    )
    buttons.append(manual_button)

    # editor button for auto populate by cycling through configured notetypes
    auto_button = editor.addButton(
        icon = icon_auto_path,
        cmd = 'autopopulate',
        func = perform_auto_cycle,
        tip="Cycle through configured notetypes to populate all fields"
    )
    buttons.append(auto_button)

# Actually adds the buttons
gui_hooks.editor_did_init_buttons.append(add_editor_buttons)

# Parse config.json as a dictionary
user_config = json.load(open("config.json"))

num_decks = len(user_config["source_decks"])
# the cap for the values in field_cycles
max_index = num_decks - 1

# list of integers that tracks how many cycles each field individually has undergone
field_cycles = []
# fills list with number of 0s equivalent to number of fields to search from
# i.e. if you are populating 5 fields, this list will have 5 integers
num_fields = len(user_config["source_fields"][0])
for i in range(num_fields):
    field_cycles.append(0)

last_cycle_was_manual = False