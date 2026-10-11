import logging

_logger = logging.getLogger(__name__)

# Public summaries of the destinations whose story in the show is well
# established. The others keep an empty summary: their page still carries the
# address and its glyphs, and the summary can be written later from the form.
#
# Planet records are loaded with noupdate="1", so the summaries are written
# here (install hook and migration) rather than in the data file.
PLANET_SUMMARIES = {
    'planet_abydos': (
        "Desert world where the Stargate programme made its first trip, in the "
        "1994 film. Home of the Abydonians, of Sha're and Skaara, and the world "
        "SG-1 returns to in the pilot episode, Children of the Gods.",
        "Monde désertique où le programme Porte des étoiles a fait son premier "
        "voyage, dans le film de 1994. Patrie des Abydoniens, de Sha're et de "
        "Skaara, et monde où SG-1 retourne dans l'épisode pilote, Children of "
        "the Gods.",
    ),
    'planet_chulak': (
        "Jaffa world ruled by the Goa'uld Apophis, and Teal'c's homeworld. SG-1 "
        "goes there in the pilot episode, where Teal'c turns against Apophis "
        "and joins the team.",
        "Monde jaffa gouverné par le Goa'uld Apophis, et monde natal de Teal'c. "
        "SG-1 s'y rend dans l'épisode pilote, où Teal'c se retourne contre "
        "Apophis et rejoint l'équipe.",
    ),
    'planet_earth': (
        "Earth, called Tau'ri by the Goa'uld. Its gate is kept by Stargate "
        "Command under Cheyenne Mountain, Colorado. Dialed from another world, "
        "this is the address that brings a team home.",
        "La Terre, appelée Tau'ri par les Goa'uld. Sa Porte est gardée par le "
        "Stargate Command, sous la montagne Cheyenne, au Colorado. Composée "
        "depuis un autre monde, c'est l'adresse qui ramène une équipe à la "
        "maison.",
    ),
    'planet_tollan': (
        "Original homeworld of the Tollan, a human civilisation far ahead of "
        "Earth. In the first-season episode Enigma, SG-1 evacuates the "
        "survivors as the planet tears itself apart.",
        "Monde d'origine des Tollans, une civilisation humaine très en avance "
        "sur la Terre. Dans l'épisode Enigma de la première saison, SG-1 "
        "évacue les survivants alors que la planète se disloque.",
    ),
    'planet_tollana': (
        "The world the Tollan settled after losing their homeworld. They keep "
        "their technology to themselves, and refuse to share it with Earth.",
        "Le monde où les Tollans se sont installés après la perte de leur "
        "planète. Ils gardent leur technologie pour eux et refusent de la "
        "partager avec la Terre.",
    ),
    'planet_othala': (
        "Homeworld of the Asgard, in the Ida galaxy. Reaching it takes an "
        "eighth symbol and far more power than a single gate gives: O'Neill "
        "dials it in The Fifth Race.",
        "Monde natal des Asgard, dans la galaxie d'Ida. Il faut un huitième "
        "symbole et bien plus d'énergie qu'une Porte seule n'en fournit : "
        "O'Neill la compose dans l'épisode The Fifth Race.",
    ),
    'planet_edora': (
        "Farming world where O'Neill is stranded after a meteor storm buries "
        "the gate, in the episode A Hundred Days.",
        "Monde agricole où O'Neill reste bloqué après qu'une pluie de "
        "météores a enseveli la Porte, dans l'épisode A Hundred Days.",
    ),
    'planet_euronda': (
        "World of the Eurondans, who ask Earth for help in their war, in the "
        "episode The Other Side. SG-1 learns what that war is about, and walks "
        "away.",
        "Monde des Eurondiens, qui demandent l'aide de la Terre dans leur "
        "guerre, dans l'épisode The Other Side. SG-1 découvre l'objet de cette "
        "guerre, et s'en retire.",
    ),
    'planet_ktau': (
        "World protected by the Asgard. In the episode Red Sky, a dialing from "
        "SG-1 turns its sun red, and the team has to undo it.",
        "Monde protégé par les Asgard. Dans l'épisode Red Sky, une "
        "connexion de SG-1 fait virer son soleil au rouge, et l'équipe doit "
        "réparer les dégâts.",
    ),
    'planet_kheb': (
        "World where Oma Desala, an ascended being, keeps watch. SG-1 seeks it "
        "out in the episode Maternal Instinct.",
        "Monde où veille Oma Desala, un être élevé. SG-1 le cherche dans "
        "l'épisode Maternal Instinct.",
    ),
    'planet_land_of_light': (
        "Planet of the Land of Light, where SG-1 meets a disease that turns "
        "people into primitives, in the first-season episode The Broca Divide.",
        "Planète du Pays de lumière, où SG-1 rencontre une maladie qui rend les "
        "gens primitifs, dans l'épisode The Broca Divide de la première "
        "saison.",
    ),
    'planet_martin_lloyd': (
        "Homeworld of Martin Lloyd, the alien living on Earth who believes he "
        "is a conspiracy theorist, in the episode Point of No Return.",
        "Monde d'origine de Martin Lloyd, l'extraterrestre installé sur Terre "
        "qui se croit adepte des théories du complot, dans l'épisode Point of "
        "No Return.",
    ),
    'planet_nid_base': (
        "Off-world base of a rogue cell of the NID, stealing alien technology "
        "behind Stargate Command's back, in the episode Shades of Grey.",
        "Base hors du monde d'une cellule dissidente du NID, qui vole des "
        "technologies extraterrestres dans le dos du Stargate Command, dans "
        "l'épisode Shades of Grey.",
    ),
}

# The address book, in every language the site carries.
MENU_LABELS = {'en_US': "Gate addresses", 'fr_FR': "Adresses de la Porte"}
MENU_URL = '/stargate/addresses'


def _installed(env, codes):
    return set(codes) & set(env['res.lang'].search([]).mapped('code'))


def set_planet_summaries(env):
    """Write the public summaries, English first: it is the source language."""
    langs = _installed(env, ('en_US', 'fr_FR'))
    for xmlid, (english, french) in PLANET_SUMMARIES.items():
        planet = env.ref('chti_stargate.%s' % xmlid, raise_if_not_found=False)
        if not planet:
            _logger.warning("Destination %s not found, summary skipped", xmlid)
            continue
        if planet.summary:
            continue  # written by hand: keep it
        # Source first, then the translation through the API made for it:
        # writing fr_FR on a field that only has its English value rewrites
        # the English one too.
        planet.with_context(lang='en_US').summary = english
        if 'fr_FR' in langs:
            planet.update_field_translations('summary', {'fr_FR': french})


def add_address_menu(env):
    """Link the address book from every website's main menu, once."""
    Menu = env['website.menu']
    for website in env['website'].search([]):
        root = website.menu_id
        if not root or Menu.search_count([
            ('website_id', '=', website.id), ('url', '=', MENU_URL),
        ]):
            continue
        after = Menu.search([
            ('parent_id', '=', root.id), ('url', '=', '/stargate'),
        ], limit=1)
        menu = Menu.with_context(lang='en_US').create({
            'name': MENU_LABELS['en_US'],
            'url': MENU_URL,
            'parent_id': root.id,
            'website_id': website.id,
            'sequence': (after.sequence + 1) if after else 50,
        })
        if 'fr_FR' in _installed(env, MENU_LABELS):
            menu.update_field_translations('name', {'fr_FR': MENU_LABELS['fr_FR']})


def post_init_hook(env):
    set_planet_summaries(env)
    add_address_menu(env)
