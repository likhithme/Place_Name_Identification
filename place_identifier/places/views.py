from django.shortcuts import render
from .forms import SentenceForm
import spacy
import wikipedia
from urllib.parse import quote
import json
import os
from fuzzywuzzy import process

# Load spaCy model
nlp = spacy.load('en_core_web_md')

# Set user agent for Wikipedia
wikipedia.set_lang("en")
wikipedia.set_user_agent("PlaceIdentifierApp/1.0 (your_actual_email@example.com)")

# Load places data from JSON file
def load_places_data():
    file_path = os.path.join(os.path.dirname(__file__), 'places_data.json')
    with open(file_path, 'r') as file:
        return json.load(file)

known_places = load_places_data()

def get_wikipedia_summary(place_name):
    # First check predefined places data
    if place_name in known_places:
        place_info = known_places[place_name]
        return place_info['summary'], place_info['url']

    try:
        # Search Wikipedia for the place
        search_results = wikipedia.search(place_name)
        if search_results:
            # Use the first search result for the place
            page = wikipedia.page(search_results[0])
            summary = page.summary[:1000]  # Truncate summary to 1000 characters
            page_url = page.url
            return summary, page_url

        return "No information available for this place.", ""

    except wikipedia.exceptions.DisambiguationError as e:
        # Handle disambiguation
        for option in e.options:
            try:
                page = wikipedia.page(option)
                summary = page.summary[:1000]  # Truncate summary to 1000 characters
                page_url = page.url
                return summary, page_url
            except wikipedia.exceptions.DisambiguationError:
                continue
            except wikipedia.exceptions.PageError:
                continue
        return "Multiple entries found for this place.", f"https://en.wikipedia.org/wiki/{quote(place_name.replace(' ', '_'))}"
    except wikipedia.exceptions.PageError:
        return "No information available for this place.", ""
    except Exception as e:
        return f"An error occurred: {str(e)}", ""

def identify_place(sentence):
    doc = nlp(sentence)
    identified_places = set()  # Use a set to avoid duplicates

    # Check spaCy NER
    for ent in doc.ents:
        if ent.label_ in ['GPE', 'LOC']:  # GPE for Geo-Political Entity, LOC for Location
            place_name = ent.text.strip()
            identified_places.add(place_name)

    # Fuzzy matching to handle misspellings
    sentence_lower = sentence.lower()
    predefined_place_names = list(known_places.keys())
    for place in predefined_place_names:
        if process.extractOne(place.lower(), [sentence_lower])[1] > 80:  # Threshold for fuzzy matching
            identified_places.add(place)

    return list(identified_places)

def index(request):
    form = SentenceForm()
    identified_places = []

    if request.method == 'POST':
        form = SentenceForm(request.POST)
        if form.is_valid():
            sentence = form.cleaned_data['sentence']
            identified_places = identify_place(sentence)

    return render(request, 'places/index.html', {'form': form, 'identified_places': identified_places})

def place_detail(request, place_name):
    summary, page_url = get_wikipedia_summary(place_name)
    return render(request, 'places/place_detail.html', {'place_name': place_name, 'summary': summary, 'page_url': page_url})
