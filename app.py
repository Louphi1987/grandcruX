from flask import Flask, request, jsonify, render_template, redirect, url_for, send_from_directory
from flask_mail import Mail, Message
import os
from database_handler import DatabaseHandler
import numpy as np
from datetime import datetime
from fpdf import FPDF
from flask_cors import CORS
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from io import BytesIO

app = Flask(__name__)

load_dotenv()
# Connexion à la base de données PostgreSQL
database_url = os.getenv("DATABASE_URL")
print("URL de la base de données :", database_url)

db_handler = DatabaseHandler(database_url=database_url)

#SERVEUR OVH: 'ssl0.ovh.net', PORT OVH: 465: SSL: True
#SERVEUR GMAIL: 'smtp.gmail.com', PORT GMAIL: 587: SSL: False
app.config['MAIL_SERVER'] = 'ssl0.ovh.net'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'noreply@grandcrux.com'
app.config['MAIL_PASSWORD'] = os.getenv("EMAIL_PASSWORD")
app.config['MAIL_DEFAULT_SENDER'] ='noreply@grandcrux.com'

mail = Mail(app)

def clean_text(txt):
    """
    Nettoie le texte pour éviter les erreurs d'encodage avec FPDF (Helvetica non Unicode).
    Remplace les apostrophes typographiques, guillemets, tirets et caractères spéciaux courants.
    """
    if not txt:
        return ""

    return (
        txt.replace("’", "'")
           .replace("‘", "'")
           .replace("‛", "'")
           .replace("“", '"')
           .replace("”", '"')
           .replace("„", '"')
           .replace("«", '"')
           .replace("»", '"')
           .replace("–", "-")
           .replace("—", "-")
           .replace("−", "-")
           .replace("…", "...")
           .replace("•", "-")
           .replace("€", "EUR")
           .replace("°", " deg ")
           .replace("¼", "1/4")
           .replace("½", "1/2")
           .replace("¾", "3/4")
           .replace("\u00A0", " ")  # espace insécable
           .replace("\u202F", " ")  # espace fine insécable
           .strip()
    )

def generate_pdf(**data):
    pdf = FPDF()
    pdf.add_page()

    # === Logo centré ===
    image_path = "static/grandcrux.png"
    page_width = pdf.w
    img_width = 100
    img_x = (page_width - img_width) / 2
    img_y = 5
    pdf.image(image_path, x=img_x, y=img_y, w=img_width)

    pdf.set_font("Helvetica", style='B', size=20)
    pdf.set_text_color(128, 0, 32)  # bordeaux

    page_height = pdf.h
    block_height = 20 + 10 + 10
    start_y = (page_height - block_height) / 2 - 10
    pdf.set_y(start_y)

    lang = data.get("lang", "fr")
    prenom = data.get("prenom", "")
    nom = data.get("nom", "")

    # === Titres traduits ===
    titres_intro = {
        "fr": (
            f"Rapport personnalisé sur le vin\n{prenom} {nom}"
        ),
        "en": (
            f"Personalized Wine Report\n{prenom} {nom}"
        ),
        "nl": (
            f"Gepersonaliseerd wijnrapport\n{prenom} {nom}"
        )
    }

    titre = titres_intro.get(lang, titres_intro["fr"])

    pdf.multi_cell(0, 12, txt=titre, align="C")

    # === Ligne décorative ===
    pdf.set_draw_color(128, 0, 32)
    pdf.set_line_width(0.8)
    line_margin = 60
    current_y = pdf.get_y()
    pdf.line(line_margin, current_y + 3, pdf.w - line_margin, current_y + 3)

    pdf.ln(15)

    pdf.add_page()

    # === Ajout du canevas (fond décoratif) ===
    canevas_path = "static/canevas.jpg"
    if os.path.exists(canevas_path):
        pdf.image(canevas_path, x=0, y=0, w=210, h=297)

    # === Titre "Introduction" couleur vin (multilingue) ===
    pdf.set_font("Helvetica", style="B", size=22)
    pdf.set_text_color(128, 0, 32)  # rouge bordeaux
    pdf.ln(17)

    lang = data.get("lang", "fr")

    titre_intro = {
        "fr": "Introduction",
        "en": "Introduction",
        "nl": "Inleiding"
    }

    pdf.cell(0, 20, titre_intro.get(lang, "Introduction"), ln=True, align="C")

    # === Ligne décorative sous le titre ===
    pdf.set_draw_color(128, 0, 32)
    pdf.set_line_width(0.8)
    page_width = pdf.w
    margin = 60
    y_line = pdf.get_y()
    pdf.line(margin, y_line, page_width - margin, y_line)
    pdf.ln(15)

    # === Corps de texte (noir) ===
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", size=12)

    # --- 1️⃣ Définition des 3 versions ---
    texte_intro_fr = (
        "Chez GrandcruX, nous pensons que chaque amateur de vin possède ses propres préférences, "
        "ses convictions et sa manière d'appréhender le plaisir comme la valeur d'une bouteille. "
        "Avant chaque achat ou investissement, il est essentiel de s'informer, de comprendre les "
        "enjeux et les opportunités qu'offre cet univers unique. "
        "\n\nCe document n'a pas vocation à fournir de conseils en matière financière ou juridique. "
        "Il s'agit avant tout d'une présentation personnalisée visant à vous informer et à nourrir "
        "votre réflexion, afin de faire de votre passion pour le vin une démarche éclairée et durable."
    )

    texte_intro_nl = (
        "Bij GrandcruX geloven wij dat elke wijnliefhebber zijn eigen voorkeuren, "
        "overtuigingen en manier heeft om het plezier en de waarde van een fles te benaderen. "
        "Voor elke aankoop of investering is het essentieel om zich goed te informeren, "
        "de uitdagingen en kansen van deze unieke wereld te begrijpen. "
        "\n\nDit document is niet bedoeld als financieel of juridisch advies. "
        "Het is bovenal een persoonlijke voorstelling die u wil informeren en inspireren, "
        "zodat uw passie voor wijn een doordachte en duurzame benadering wordt."
    )

    texte_intro_en = (
        "At GrandcruX, we believe that every wine enthusiast has their own preferences, "
        "convictions, and way of appreciating both the pleasure and the value of a bottle. "
        "Before any purchase or investment, it is essential to stay informed, to understand "
        "the challenges and opportunities offered by this unique world. "
        "\n\nThis document is not intended to provide financial or legal advice. "
        "It is above all a personalized presentation designed to inform and inspire you, "
        "so that your passion for wine becomes an enlightened and sustainable pursuit."
    )

    lang = data.get("lang", "fr")

    textes_intro = {
        "fr": texte_intro_fr,
        "nl": texte_intro_nl,
        "en": texte_intro_en
    }

    # --- 3️⃣ Écriture du texte adapté dans le PDF ---
    pdf.multi_cell(0, 8, txt=textes_intro.get(lang, texte_intro_fr), align="L")
    pdf.ln(10)

    pdf.add_page()
    canevas_path = "static/canevas.jpg"
    if os.path.exists(canevas_path):
        pdf.image(canevas_path, x=0, y=0, w=210, h=297)

    # === Titre couleur vin (multilingue) ===
    pdf.set_font("Helvetica", style="B", size=22)
    pdf.set_text_color(128, 0, 32)  # rouge bordeaux
    pdf.ln(17)

    lang = data.get("lang", "fr")

    titre_vin = {
        "fr": "Votre rapport au vin et à son patrimoine",
        "en": "Your Relationship with Wine and Heritage",
        "nl": "Uw relatie met wijn en erfgoed"
    }

    pdf.cell(0, 20, titre_vin.get(lang, titre_vin["fr"]), ln=True, align="C")

    # === Ligne décorative sous le titre ===
    pdf.set_draw_color(128, 0, 32)
    pdf.set_line_width(0.8)
    page_width = pdf.w
    margin = 60
    y_line = pdf.get_y()
    pdf.line(margin, y_line, page_width - margin, y_line)
    pdf.ln(15)

    # === Corps de texte (noir) ===
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", size=12)

    # === Personnalisation selon profil (FR / NL / EN) ===

    connaissance = data.get("connaissance_vin", "")
    relation = data.get("relation_vin", "")
    lang = data.get("lang", "fr")

    # 1️⃣ Phrase d’introduction selon la langue
    phrases_intro = {
        "fr": f"Nous avons noté que vous êtes {connaissance.replace('_', ' ')} et que votre relation principale au vin est orientée vers {relation.replace('_', ' ')}.",
        "en": f"We noted that you are {connaissance.replace('_', ' ')} and that your main relationship to wine is focused on {relation.replace('_', ' ')}.",
        "nl": f"We hebben genoteerd dat u {connaissance.replace('_', ' ')} bent en dat uw belangrijkste relatie met wijn gericht is op {relation.replace('_', ' ')}."
    }
    phrase_intro = phrases_intro.get(lang, phrases_intro["fr"])

    # 2️⃣ Texte selon niveau de connaissance
    textes_connaissance = {
        "fr": {
            "debutant": (
                "Votre intérêt pour le vin constitue un excellent point de départ. "
                "Le monde du vin est vaste et passionnant : apprendre à distinguer les régions, les millésimes et les styles "
                "est une démarche enrichissante qui peut se vivre à travers la dégustation, la lecture ou la visite de domaines."
            ),
            "amateur": (
                "Votre profil d’amateur éclairé traduit une curiosité solide pour le vin. "
                "Approfondir vos connaissances sur les producteurs, les terroirs et les millésimes vous permettra d’affiner votre sélection "
                "et de renforcer la dimension plaisir et culturelle de votre cave."
            ),
            "connaisseur": (
                "Votre profil de connaisseur(se) ou collectionneur(se) révèle une approche experte du vin. "
                "Vous êtes sans doute attentif(ve) à la provenance, à la conservation et à la rareté, des éléments essentiels pour préserver "
                "la valeur culturelle et potentielle de vos bouteilles dans le temps."
            ),
            "professionnel": (
                "Votre profil de professionnel(le) du vin implique une compréhension approfondie du marché. "
                "Votre expérience vous permet d’envisager le vin comme un univers à la fois économique, sensoriel et culturel. "
                "Ce document vise avant tout à compléter cette expertise par une perspective patrimoniale."
            ),
            "autre": (
                "Votre rapport au vin témoigne d’un intérêt authentique pour cet univers de passion et de transmission. "
                "Chaque approche du vin est unique, qu’elle soit gustative, culturelle ou patrimoniale."
            ),
        },
        "en": {
            "debutant": (
                "Your interest in wine is an excellent starting point. "
                "The world of wine is vast and fascinating: learning to distinguish regions, vintages, and styles "
                "is a rewarding journey that can be experienced through tasting, reading, and visiting estates."
            ),
            "amateur": (
                "Your profile as an informed wine enthusiast shows a strong curiosity. "
                "Deepening your knowledge of producers, terroirs, and vintages will refine your selections "
                "and strengthen the pleasure and cultural dimension of your cellar."
            ),
            "connaisseur": (
                "Your profile as a connoisseur or collector reflects an expert approach to wine. "
                "You are likely attentive to provenance, storage, and rarity — key aspects for preserving "
                "the cultural and potential value of your bottles over time."
            ),
            "professionnel": (
                "Your profile as a wine professional implies a deep understanding of the market. "
                "Your experience allows you to see wine as both an economic, sensory, and cultural universe. "
                "This document aims to complement that expertise with a patrimonial perspective."
            ),
            "autre": (
                "Your relationship with wine reflects a genuine interest in this world of passion and heritage. "
                "Each approach to wine is unique — gustatory, cultural, or patrimonial."
            ),
        },
        "nl": {
            "debutant": (
                "Uw interesse in wijn vormt een uitstekend vertrekpunt. "
                "De wijnwereld is rijk en boeiend: het leren onderscheiden van regio’s, jaargangen en stijlen "
                "is een verrijkende ervaring die men kan beleven via proeverijen, lectuur of bezoeken aan wijnhuizen."
            ),
            "amateur": (
                "Uw profiel als goed geïnformeerde wijnliefhebber toont een sterke nieuwsgierigheid. "
                "Door uw kennis van producenten, terroirs en jaargangen te verdiepen, kunt u uw keuzes verfijnen "
                "en het plezier en de culturele dimensie van uw kelder versterken."
            ),
            "connaisseur": (
                "Uw profiel als kenner of verzamelaar weerspiegelt een deskundige benadering van wijn. "
                "U hecht waarschijnlijk belang aan herkomst, bewaring en zeldzaamheid — essentiële elementen "
                "voor het behoud van de culturele en potentiële waarde van uw flessen op lange termijn."
            ),
            "professionnel": (
                "Uw profiel als wijnprofessional impliceert een grondig begrip van de markt. "
                "Uw ervaring laat u toe wijn te benaderen als zowel een economisch, zintuiglijk als cultureel universum. "
                "Dit document wil die expertise aanvullen met een patrimoniale invalshoek."
            ),
            "autre": (
                "Uw relatie tot wijn getuigt van een oprechte belangstelling voor deze wereld van passie en overdracht. "
                "Elke benadering van wijn is uniek, of ze nu smaakgericht, cultureel of patrimoniaal is."
            ),
        }
    }

    texte_connaissance = textes_connaissance.get(lang, textes_connaissance["fr"]).get(connaissance,
                                                                                      textes_connaissance[lang][
                                                                                          "autre"])

    # 3️⃣ Texte selon relation au vin
    textes_relation = {
        "fr": {
            "consommation": (
                "Le vin reste avant tout un produit de plaisir et de convivialité. "
                "L’apprécier dans un cadre personnel ou familial fait partie intégrante de son essence culturelle. "
                "Choisir, déguster et conserver le vin permettent de tisser un lien vivant avec le patrimoine et les traditions viticoles."
            ),
            "investissement": (
                "Vous semblez envisager le vin comme un placement. "
                "Il convient toutefois de rappeler que le vin n’est pas un produit financier mais un bien tangible dont la valeur dépend de nombreux facteurs : "
                "millésime, conservation, rareté, notoriété du domaine et conditions de marché. "
                "Les informations fournies ici sont d’ordre général et ne constituent en aucun cas une recommandation en matière d’investissement."
            ),
            "les_deux": (
                "Vous associez à la fois plaisir et approche patrimoniale dans votre rapport au vin. "
                "C’est une vision équilibrée, à condition de toujours garder à l’esprit que le vin reste avant tout un produit de passion. "
                "Toute considération financière doit être envisagée avec prudence, en tenant compte des aléas du marché et des conditions de conservation. "
                "Les éléments présentés dans ce document n’ont pas vocation à constituer un conseil en investissement."
            ),
            "autre": (
                "Votre lien au vin illustre une approche personnelle et sincère, ancrée dans la découverte et le plaisir. "
                "Chaque bouteille représente une expérience unique et un fragment de patrimoine vivant."
            ),
        },
        "en": {
            "consommation": (
                "Wine is above all a product of pleasure and conviviality. "
                "Enjoying it in a personal or family setting is part of its cultural essence. "
                "Choosing, tasting, and storing wine creates a living connection to heritage and tradition."
            ),
            "investissement": (
                "You seem to consider wine as an investment. "
                "It should be remembered, however, that wine is not a financial product but a tangible good whose value depends on many factors: "
                "vintage, storage, rarity, reputation of the estate, and market conditions. "
                "The information provided here is general and should not be taken as investment advice."
            ),
            "les_deux": (
                "You combine both pleasure and patrimonial perspective in your approach to wine. "
                "This is a balanced vision, provided you keep in mind that wine remains first and foremost a product of passion. "
                "Any financial consideration must be approached with prudence, taking into account market fluctuations and storage conditions. "
                "The information presented here does not constitute investment advice."
            ),
            "autre": (
                "Your connection to wine reflects a sincere and personal approach rooted in discovery and pleasure. "
                "Each bottle represents a unique experience and a living piece of heritage."
            ),
        },
        "nl": {
            "consommation": (
                "Wijn is bovenal een product van plezier en gezelligheid. "
                "Het waarderen ervan in een persoonlijke of familiale context maakt deel uit van zijn culturele essentie. "
                "Het kiezen, proeven en bewaren van wijn schept een levendige band met het erfgoed en de tradities van de wijnbouw."
            ),
            "investissement": (
                "U lijkt wijn te beschouwen als een vorm van investering. "
                "Het is echter belangrijk te onthouden dat wijn geen financieel product is, maar een tastbaar goed waarvan de waarde afhangt van vele factoren: "
                "jaargang, bewaring, zeldzaamheid, reputatie van het domein en marktomstandigheden. "
                "De hier verstrekte informatie is algemeen en vormt op geen enkele manier beleggingsadvies."
            ),
            "les_deux": (
                "U combineert plezier en een patrimoniale benadering in uw relatie tot wijn. "
                "Dat is een evenwichtige visie, op voorwaarde dat men niet vergeet dat wijn in de eerste plaats een product van passie blijft. "
                "Elke financiële overweging moet met voorzichtigheid worden bekeken, rekening houdend met markt- en bewaaromstandigheden. "
                "De informatie in dit document is louter informatief en vormt geen beleggingsadvies."
            ),
            "autre": (
                "Uw band met wijn weerspiegelt een persoonlijke en oprechte benadering, geworteld in ontdekking en plezier. "
                "Elke fles vertegenwoordigt een unieke ervaring en een levend stuk cultureel erfgoed."
            ),
        }
    }

    texte_relation = textes_relation.get(lang, textes_relation["fr"]).get(relation, textes_relation[lang]["autre"])

    # 4️⃣ Écriture dans le PDF
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 8, txt=clean_text(phrase_intro), align="L")
    pdf.ln(6)
    pdf.multi_cell(0, 8, txt=clean_text(texte_connaissance), align="L")
    pdf.ln(6)
    pdf.multi_cell(0, 8, txt=clean_text(texte_relation), align="L")
    pdf.ln(10)

    # === Phrase d’introduction selon la région viticole choisie (FR / NL / EN) ===

    region = data.get("region_preferee", "")
    lang = data.get("lang", "fr")

    # On définit d’abord la phrase standard
    phrases_region = {
        "fr": f"Vous avez exprimé une préférence pour la région viticole suivante : {region.replace('_', ' ')}.",
        "en": f"You have expressed a preference for the following wine region: {region.replace('_', ' ')}.",
        "nl": f"U hebt een voorkeur aangegeven voor de volgende wijnregio: {region.replace('_', ' ')}."
    }

    # Puis on définit une phrase spécifique pour “autre”
    phrases_region_autre = {
        "fr": (
            "Vous avez indiqué ne pas avoir de préférence particulière pour une région viticole. "
            "Cela peut être une excellente occasion d’explorer plusieurs horizons et de recevoir des conseils personnalisés "
            "selon vos goûts et objectifs."
        ),
        "en": (
            "You mentioned not having a specific preference for any wine region. "
            "This can be a great opportunity to explore various options and receive personalized guidance "
            "based on your tastes and goals."
        ),
        "nl": (
            "U hebt aangegeven geen specifieke voorkeur te hebben voor een wijnregio. "
            "Dit biedt een mooie gelegenheid om verschillende horizonten te verkennen en persoonlijk advies te ontvangen "
            "volgens uw smaak en doelstellingen."
        )
    }

    # Sélection automatique de la phrase selon le cas
    if region == "autre":
        phrase_intro_region = phrases_region_autre.get(lang, phrases_region_autre["fr"])
    else:
        phrase_intro_region = phrases_region.get(lang, phrases_region["fr"])

    # Écriture dans le PDF
    pdf.multi_cell(0, 8, txt=clean_text(phrase_intro_region), align="L")
    pdf.ln(6)

    # Texte selon la région
    textes_region = {
        "fr": {
            "bordeaux": (
                "La région de Bordeaux est une référence mondiale, connue pour ses grands crus classés et son équilibre entre puissance et élégance. "
                "C’est une excellente approche pour comprendre la notion de terroir et de longévité des vins.\n\n"
                "Posez-vous la question : préférez-vous les vins de la rive gauche (Cabernet Sauvignon, Médoc) ou de la rive droite (Merlot, Saint-Émilion) ?\n\n"
                "Quelques noms emblématiques : Château Margaux, Lafite Rothschild, Pétrus, Cheval Blanc."
            ),
            "bourgogne": (
                "La Bourgogne séduit par son raffinement et sa complexité. C’est une région de vignerons, où chaque parcelle raconte une histoire. "
                "S’intéresser à la Bourgogne, c’est explorer la subtilité des climats et l’expression du Pinot Noir et du Chardonnay.\n\n"
                "Posez-vous la question : préférez-vous les rouges structurés (Côte de Nuits) ou les blancs prestigieux (Côte de Beaune) ? \n\n"
                "Quelques noms : Romanée-Conti, Meursault, Puligny-Montrachet, Chambertin."
            ),
            "vallee_du_rhone": (
                "La Vallée du Rhône offre des vins généreux, solaires et puissants. "
                "Du nord (Côte-Rôtie, Hermitage) au sud (Châteauneuf-du-Pape), la diversité y est remarquable.\n\n"
                "Posez-vous la question : recherchez-vous des vins à forte identité (Syrah) ou plus épicés et ronds (Grenache, Mourvèdre) ?\n\n"
                "Quelques domaines réputés : E. Guigal, Chapoutier, Château de Beaucastel."
            ),
            "loire": (
                "La Loire est un fleuve de fraîcheur et de diversité : rouges, blancs, rosés ou effervescents, elle a tout pour plaire. "
                "C’est une région idéale pour les amateurs de vins digestes et francs.\n\n"
                "Posez-vous la question : êtes-vous plutôt Sauvignon (Sancerre, Pouilly-Fumé) ou Chenin (Vouvray, Anjou) ?\n\n"
                "Quelques producteurs : Didier Dagueneau, Huet, Domaine des Roches Neuves."
            ),
            "champagne": (
                "Le Champagne allie tradition et prestige. Derrière les bulles se cache un savoir-faire exceptionnel. "
                "S’intéresser au Champagne, c’est comprendre l’art de l’assemblage et la patience du vieillissement.\n\n"
                "Posez-vous la question : préférez-vous les grandes maisons (Dom Pérignon, Bollinger) ou les vignerons indépendants (Jacques Selosse, Egly-Ouriet) ?"
            ),
            "alsace": (
                "L’Alsace séduit par ses vins aromatiques et précis. Riesling, Gewurztraminer, Pinot Gris… chaque cépage y révèle sa pureté. "
                "Posez-vous la question : aimez-vous les vins secs et tendus, ou plus riches et exotiques ? \n\n"
                "Quelques domaines : Trimbach, Zind-Humbrecht, Weinbach.\n\n"
            ),
            "provence": (
                "La Provence évoque la douceur du Sud et la convivialité. Si ses rosés sont célèbres, ses rouges et blancs gagnent aussi en noblesse.\n\n"
                "Posez-vous la question : cherchez-vous un vin d’été ou un vin de gastronomie ? \n\n"
                "Quelques domaines : Domaine Tempier, Château d’Esclans, Minuty, Ott."
            ),
            "italie": (
                "L’Italie est un continent viticole à elle seule, avec des vins de caractère et d’identité. "
                "Du Piémont (Barolo, Barbaresco) à la Toscane (Brunello, Chianti, Super Toscans), la diversité est immense.\n\n"
                "Posez-vous la question : aimez-vous les vins puissants et tanniques, ou plus élégants et floraux ? \n\n"
                "Quelques icônes : Gaja, Antinori, Sassicaia, Ornellaia."
            ),
            "espagne": (
                "L’Espagne combine tradition et renouveau, avec des terroirs remarquables. "
                "Du Rioja à la Ribera del Duero, les Tempranillo offrent puissance et velours. \n\n"
                "Posez-vous la question : recherchez-vous un vin boisé et intense, ou plus moderne et fruité ? \n\n"
                "Quelques domaines : Vega Sicilia, Alvaro Palacios, La Rioja Alta."
            ),
            "portugal": (
                "Le Portugal, longtemps discret, séduit aujourd’hui par son authenticité. "
                "Au-delà des vins de Porto, on y trouve de grands rouges du Douro et de l’Alentejo. \n\n"
                "Posez-vous la question : préférez-vous la tradition des vins mutés ou la modernité des vins tranquilles ? \n\n"
                "Quelques références : Niepoort, Quinta do Noval, Esporão."
            ),
            "nouveau_monde": (
                "Les vins du Nouveau Monde incarnent la modernité et la liberté de style : Chili, Argentine, Australie, Californie, Nouvelle-Zélande... \n\n"
                "Posez-vous la question : préférez-vous la puissance du soleil ou la fraîcheur du fruit ? \n\n"
                "Quelques producteurs emblématiques : Penfolds (Australie), Catena Zapata (Argentine), Opus One (États-Unis)."
            ),
            "autre": (
                "Chaque région du monde offre ses trésors et ses particularités. \n\n"
                "Il existe de nombreuses options passionnantes selon vos goûts et vos objectifs. \n\n"
                "N’hésitez pas à nous contacter pour en discuter avec un conseiller GrandcruX : nous serons ravis de vous orienter vers les meilleures découvertes."
            ),
        },

        # 🇬🇧 ENGLISH VERSION
        "en": {
            "bordeaux": (
                "The Bordeaux region is a global benchmark, known for its classified growths and balance between power and elegance. "
                "It’s ideal for understanding the notion of terroir and wine longevity. \n\n"
                "Ask yourself: do you prefer Left Bank wines (Cabernet Sauvignon, Médoc) or Right Bank (Merlot, Saint-Émilion)? \n\n"
                "Notable names include Château Margaux, Lafite Rothschild, Pétrus, Cheval Blanc."
            ),
            "bourgogne": (
                "Burgundy seduces with its refinement and complexity. It’s a region of growers where every parcel tells a story. "
                "Exploring Burgundy means discovering the subtleties of terroir through Pinot Noir and Chardonnay. \n\n"
                "Ask yourself: do you prefer structured reds (Côte de Nuits) or prestigious whites (Côte de Beaune)? \n\n"
                "Icons include Romanée-Conti, Meursault, Puligny-Montrachet, Chambertin."
            ),
            "vallee_du_rhone": (
                "The Rhône Valley offers generous, sun-filled, and powerful wines. "
                "From the north (Côte-Rôtie, Hermitage) to the south (Châteauneuf-du-Pape), diversity abounds. \n\n"
                "Ask yourself: do you prefer Syrah’s character or the round, spicy blends of Grenache and Mourvèdre? \n\n"
                "Renowned estates: E. Guigal, Chapoutier, Château de Beaucastel."
            ),
            "loire": (
                "The Loire embodies freshness and diversity: reds, whites, rosés, and sparkling wines. "
                "It’s perfect for those who love bright, lively wines. \n\n"
                "Ask yourself: Sauvignon (Sancerre, Pouilly-Fumé) or Chenin (Vouvray, Anjou)? \n\n"
                "Recommended producers: Didier Dagueneau, Huet, Domaine des Roches Neuves."
            ),
            "champagne": (
                "Champagne combines prestige and tradition. Behind the bubbles lies centuries of craftsmanship. \n\n"
                "Ask yourself: do you prefer great houses (Dom Pérignon, Bollinger) or grower champagnes (Jacques Selosse, Egly-Ouriet)?"
            ),
            "alsace": (
                "Alsace shines through its aromatic and precise wines — Riesling, Gewurztraminer, Pinot Gris. \n\n"
                "Ask yourself: do you enjoy dry, crisp wines or richer, exotic ones? \n\n"
                "Key estates: Trimbach, Zind-Humbrecht, Weinbach."
            ),
            "provence": (
                "Provence evokes warmth and conviviality. Known for its rosés, it also produces elegant reds and whites. \n\n"
                "Ask yourself: do you seek a summer wine or a gastronomic one? \n\n"
                "Top names: Domaine Tempier, Château d’Esclans, Minuty, Ott."
            ),
            "italie": (
                "Italy is a world of wine on its own, full of diversity and soul. "
                "From Piedmont (Barolo, Barbaresco) to Tuscany (Brunello, Chianti, Super Tuscans), the range is immense. \n\n"
                "Ask yourself: powerful and tannic, or floral and refined? \n\n"
                "Famous producers: Gaja, Antinori, Sassicaia, Ornellaia."
            ),
            "espagne": (
                "Spain blends tradition and innovation. From Rioja to Ribera del Duero, Tempranillo expresses depth and elegance. \n\n"
                "Ask yourself: do you prefer classic, oaky wines or modern, fruit-forward styles? \n\n"
                "Key producers: Vega Sicilia, Alvaro Palacios, La Rioja Alta."
            ),
            "portugal": (
                "Portugal’s charm lies in its authenticity. Beyond Port, great red wines from Douro and Alentejo deserve attention. \n\n"
                "Ask yourself: fortified heritage or modern still wines? \n\n"
                "Recommended estates: Niepoort, Quinta do Noval, Esporão."
            ),
            "nouveau_monde": (
                "The New World represents modernity and creativity — from Chile and Argentina to Australia and California. \n\n"
                "Ask yourself: do you prefer power or fruit freshness? \n\n"
                "Notable producers: Penfolds, Catena Zapata, Opus One."
            ),
            "autre": (
                "Every region has its hidden gems and stories. \n\n"
                "There are many fascinating possibilities depending on your tastes and goals. \n\n"
                "Do not hesitate to contact a GrandcruX advisor for a personalized discussion."
            ),
        },

        # 🇳🇱 DUTCH VERSION
        "nl": {
            "bordeaux": (
                "De Bordeauxstreek is een wereldwijde referentie, bekend om haar geclassificeerde wijnen en haar balans tussen kracht en elegantie. "
                "Het is een ideale regio om het begrip terroir en de lange levensduur van wijn te begrijpen. \n\n"
                "Stel uzelf de vraag: geeft u de voorkeur aan de linkeroever (Cabernet Sauvignon, Médoc) of de rechteroever (Merlot, Saint-Émilion)? \n\n"
                "Enkele iconen: Château Margaux, Lafite Rothschild, Pétrus, Cheval Blanc."
            ),
            "bourgogne": (
                "Bourgogne verleidt door haar verfijning en complexiteit. "
                "Elke wijngaard vertelt er zijn eigen verhaal, met Pinot Noir en Chardonnay als hoofdrolspelers. \n\n"
                "Stel uzelf de vraag: houdt u van gestructureerde rode wijnen (Côte de Nuits) of prestigieuze witte (Côte de Beaune)? \n\n"
                "Enkele referenties: Romanée-Conti, Meursault, Puligny-Montrachet, Chambertin."
            ),
            "vallee_du_rhone": (
                "De Rhônevallei biedt genereuze, zonnige en krachtige wijnen. "
                "Van het noorden (Côte-Rôtie, Hermitage) tot het zuiden (Châteauneuf-du-Pape) is de diversiteit indrukwekkend. \n\n"
                "Stel uzelf de vraag: verkiest u de kracht van Syrah of de kruidige rondheid van Grenache en Mourvèdre? \n\n"
                "Bekende domeinen: E. Guigal, Chapoutier, Château de Beaucastel."
            ),
            "loire": (
                "De Loire staat voor frisheid en diversiteit: rood, wit, rosé en mousserend. "
                "Ideaal voor wie houdt van levendige, evenwichtige wijnen. \n\n"
                "Stel uzelf de vraag: Sauvignon (Sancerre, Pouilly-Fumé) of Chenin (Vouvray, Anjou)? \n\n"
                "Aanbevolen producenten: Didier Dagueneau, Huet, Domaine des Roches Neuves."
            ),
            "champagne": (
                "Champagne verenigt prestige en traditie. Achter de bubbels schuilt een eeuwenoud vakmanschap. \n\n"
                "Stel uzelf de vraag: verkiest u de grote huizen (Dom Pérignon, Bollinger) of onafhankelijke wijnmakers (Jacques Selosse, Egly-Ouriet)?"
            ),
            "alsace": (
                "De Elzas betovert met haar aromatische precisie. Riesling, Gewurztraminer, Pinot Gris – elk druivenras drukt zijn eigen karakter uit. \n\n"
                "Stel uzelf de vraag: houdt u van droge, frisse wijnen of eerder van rijke en exotische stijlen? \n\n"
                "Referenties: Trimbach, Zind-Humbrecht, Weinbach."
            ),
            "provence": (
                "De Provence roept de sfeer van het Zuiden en gezelligheid op. "
                "Naast rosé produceert men er ook steeds vaker nobele rode en witte wijnen. \n\n"
                "Stel uzelf de vraag: zoekt u een zomerwijn of een gastronomische wijn? \n\n"
                "Domeinen: Domaine Tempier, Château d’Esclans, Minuty, Ott."
            ),
            "italie": (
                "Italië is een wijncontinent op zich, vol diversiteit en karakter. "
                "Van Piemonte (Barolo, Barbaresco) tot Toscane (Brunello, Chianti, Super Tuscans) is de variatie enorm. \n\n"
                "Stel uzelf de vraag: krachtig en tanninerijk of elegant en bloemig? \n\n"
                "Enkele iconen: Gaja, Antinori, Sassicaia, Ornellaia."
            ),
            "espagne": (
                "Spanje combineert traditie met vernieuwing. "
                "Van Rioja tot Ribera del Duero brengt de Tempranillo kracht en fluweelzachtheid samen. \n\n"
                "Stel uzelf de vraag: houdt u van klassieke houtgerijpte wijnen of moderne fruitige stijlen? \n\n"
                "Bekende namen: Vega Sicilia, Alvaro Palacios, La Rioja Alta."
            ),
            "portugal": (
                "Portugal charmeert door zijn authenticiteit. "
                "Naast de beroemde portwijnen biedt het Douro- en Alentejo-gebied uitstekende rode wijnen. \n\n"
                "Stel uzelf de vraag: houdt u van versterkte wijnen of moderne stille wijnen? \n\n"
                "Aanbevolen producenten: Niepoort, Quinta do Noval, Esporão."
            ),
            "nouveau_monde": (
                "De Nieuwe Wereld staat voor moderne expressie en vrijheid: Chili, Argentinië, Australië, Californië, Nieuw-Zeeland. \n\n"
                "Stel uzelf de vraag: verkiest u kracht of fruitige frisheid? \n\n"
                "Referenties: Penfolds, Catena Zapata, Opus One."
            ),
            "autre": (
                "Elke wijnregio ter wereld biedt haar eigen rijkdommen en verrassingen. \n\n"
                "Er bestaan talloze boeiende mogelijkheden, afhankelijk van uw smaak en doelstellingen. \n\n"
                "Aarzel niet om contact op te nemen met een GrandcruX-adviseur om samen de beste opties te ontdekken."
            ),
        }
    }

    # Sélection du texte
    texte_region = textes_region.get(lang, textes_region["fr"]).get(region, textes_region[lang]["autre"])

    # Écriture dans le PDF
    pdf.multi_cell(0, 8, txt=clean_text(texte_region), align="L")
    pdf.ln(10)

    pdf.add_page()
    canevas_path = "static/canevas.jpg"
    if os.path.exists(canevas_path):
        pdf.image(canevas_path, x=0, y=0, w=210, h=297)

    bouteille_path = "static/bouteille.jpg"
    pdf.set_y(30)
    if os.path.exists(bouteille_path):
        # On dessine la bouteille légèrement à gauche du texte
        y_pos = pdf.get_y()
        pdf.image(bouteille_path, x=55, y=y_pos + 1, w=8)
        text_x = 67
    else:
        text_x = 60

    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(106, 27, 27)  # bordeaux #6a1b1b
    pdf.set_x(text_x)

    lang = data.get("lang", "fr")

    titre_diversification = {
        "fr": "Le vin comme outil de diversification",
        "en": "Wine as a Tool for Diversification",
        "nl": "Wijn als middel tot diversificatie"
    }

    pdf.cell(0, 10, titre_diversification.get(lang, titre_diversification["fr"]), ln=True, align="L")
    pdf.ln(6)

    # === Corps de texte (noir) ===
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", size=12)

    budget_vin = data.get("budget_vin", "moins_500")

    textes_budget = {
        "fr": {
            "moins_500": (
                "Nous notons que vous consacrez un budget inférieur à 500 EUR par an au vin. "
                "Ce choix témoigne d’une approche mesurée et axée sur le plaisir simple, sans excès ni contrainte."
            ),
            "500_2000": (
                "Nous notons que vous consacrez un budget compris entre 500 EUR et 2 000 EUR par an au vin. "
                "Un équilibre appréciable entre plaisir et curiosité, permettant d’explorer de belles appellations tout en gardant la maîtrise de votre budget."
            ),
            "2000_10000": (
                "Nous notons que vous consacrez un budget compris entre 2 000 EUR et 10 000 EUR par an au vin. "
                "Ce niveau reflète un véritable engagement et une passion affirmée, mêlant plaisir, découverte et valorisation du patrimoine."
            ),
            "plus_10000": (
                "Nous notons que vous consacrez un budget supérieur à 10 000 EUR par an au vin. "
                "Une telle enveloppe témoigne d’un intérêt profond, voire d’une approche patrimoniale ou collectionneuse du vin."
            ),
            "explication": (
                "Nous vous invitons à un petit exercice personnel : déterminer à quel pourcentage ou fréquence vous trouvez votre satisfaction dans le vin. "
                "Si votre rapport au vin est avant tout lié à la consommation, il peut être intéressant de ressentir votre « pourcentage plaisir » — quitte, si la passion évolue, à déployer le budget en conséquence. \n\n"
                "Si votre approche s’oriente davantage vers l’investissement, nous ne fournissons pas de conseil en investissement, "
                "mais le cadre général du graphique ci-dessous pourrait vous aider à visualiser une répartition équilibrée. "
                "Le vin peut ainsi être envisagé comme un placement alternatif, au même titre que des oeuvres d’art, des voitures de collection ou des montres d’exception. "

            )
        },
        "en": {
            "moins_500": (
                "We note that you dedicate a yearly wine budget below EUR500. "
                "This suggests a measured approach focused on enjoyment and simplicity."
            ),
            "500_2000": (
                "We note that you dedicate a yearly wine budget between EUR500 and EUR2,000. "
                "A balanced level allowing you to explore interesting appellations while keeping spending under control."
            ),
            "2000_10000": (
                "We note that you dedicate a yearly wine budget between EUR2,000 and EUR10,000. "
                "This reflects a genuine enthusiasm and passion, combining pleasure, discovery, and heritage value."
            ),
            "plus_10000": (
                "We note that you dedicate a yearly wine budget above EUR10,000. "
                "Such a commitment reflects a deep passion or a collector’s mindset regarding fine wine."
            ),
            "explication": (
                "We invite you to a brief personal exercise: consider at what percentage or frequency you find your satisfaction in wine. "
                "If your relationship with wine is primarily about consumption, it may be interesting to sense your 'pleasure ratio' — and, as your passion grows, adjust your budget accordingly. \n\n"
                "If your focus leans more toward investment, please note that we do not provide investment advice; however, "
                "the general framework shown in the chart below may help you visualize a balanced proportion. "
                "Wine can thus be seen as an alternative asset, much like art, collectible cars, or fine watches. "

            )
        },
        "nl": {
            "moins_500": (
                "We merken op dat u een jaarlijks wijnbudget van minder dan EUR500 voorziet. "
                "Dit wijst op een nuchtere benadering die draait om eenvoudig genot en ontdekking."
            ),
            "500_2000": (
                "We merken op dat u een jaarlijks wijnbudget tussen EUR500 en EUR2.000 voorziet. "
                "Een mooi evenwicht tussen plezier en nieuwsgierigheid, waarmee u interessante wijnen kunt ontdekken binnen een beheersbaar budget."
            ),
            "2000_10000": (
                "We merken op dat u een jaarlijks wijnbudget tussen EUR2.000 en EUR10.000 voorziet. "
                "Dit toont een oprechte passie en betrokkenheid bij wijn, waarbij genot en waardebehoud samengaan."
            ),
            "plus_10000": (
                "We merken op dat u een jaarlijks wijnbudget van meer dan EUR10.000 voorziet. "
                "Dat getuigt van een diepe interesse of zelfs een verzamelaarshouding ten opzichte van fijne wijn."
            ),
            "explication": (
                "Wij nodigen u uit om even stil te staan bij de vraag in welke mate of frequentie wijn u voldoening schenkt. "
                "Indien uw relatie met wijn vooral betrekking heeft op consumptie, kan het interessant zijn om uw ‘plezierpercentage’ te voelen — en, naarmate de passie groeit, uw budget daarop af te stemmen. \n\n"
                "Indien u wijn eerder als investering ziet, geven wij geen beleggingsadvies, maar het algemene kader in de onderstaande grafiek kan u helpen een evenwichtige verdeling te visualiseren. "
                "Wijn kan in dat geval worden beschouwd als een alternatief beleggingsmiddel, vergelijkbaar met kunstwerken, oldtimers of luxehorloges. "
            )
        }
    }

    # Récupération du texte correspondant
    texte_budget_intro = textes_budget.get(lang, textes_budget["fr"]).get(budget_vin, textes_budget["fr"]["moins_500"])
    texte_budget_explication = textes_budget.get(lang, textes_budget["fr"])["explication"]

    # 6️⃣ Écriture dans le PDF
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 8, txt=clean_text(texte_budget_intro), align="L")
    pdf.ln(6)
    pdf.multi_cell(0, 8, txt=clean_text(texte_budget_explication), align="L")
    pdf.ln(10)

    graph_path = "static/graph.jpg"
    if os.path.exists(graph_path):
        page_width = pdf.w - 2 * pdf.l_margin
        graph_width = 80  # largeur du graphique (ajuste selon ton image)
        x_pos = (page_width - graph_width) / 2 + pdf.l_margin
        pdf.image(graph_path, x=x_pos, w=graph_width)
        pdf.ln(10)

        if budget_vin:  # si un choix de budget a été fait, peu importe lequel
            mentions = {
                "fr": "ATTENTION : Ceci ne constitue pas un conseil en investissement.",
                "en": "ATTENTION:  This does not constitute investment advice.",
                "nl": "OPGELET: Dit vormt geen beleggingsadvies."
            }
            mention_texte = mentions.get(lang, mentions["fr"])

            pdf.set_font("Helvetica", "I", 11)
            pdf.set_text_color(80, 80, 80)  # gris doux
            pdf.ln(4)
            pdf.multi_cell(0, 8, txt=clean_text(mention_texte), align="C")
            pdf.ln(10)

    pdf.add_page()
    canevas_path = "static/canevas.jpg"
    if os.path.exists(canevas_path):
        pdf.image(canevas_path, x=0, y=0, w=210, h=297)

    bouteille_path = "static/bouteille.jpg"
    pdf.set_y(30)
    if os.path.exists(bouteille_path):
        # On dessine la bouteille légèrement à gauche du texte
        y_pos = pdf.get_y()
        pdf.image(bouteille_path, x=35, y=y_pos + 1, w=8)
        text_x = 48
    else:
        text_x = 43

    # === Titre "Conserver et valoriser le vin comme un patrimoine" (multilingue) ===
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(106, 27, 27)  # bordeaux #6a1b1b
    pdf.set_x(text_x)

    lang = data.get("lang", "fr")

    titre_patrimoine = {
        "fr": "Conserver et valoriser le vin comme un patrimoine",
        "en": "Preserving and Enhancing Wine as Heritage",
        "nl": "Wijn bewaren en waarderen als erfgoed"
    }

    pdf.cell(0, 10, titre_patrimoine.get(lang, titre_patrimoine["fr"]), ln=True, align="L")
    pdf.ln(6)

    # === Corps de texte (noir) ===
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", size=12)

    forme_possession = data.get("forme_possession", "pas_encore")
    motivation = data.get("motivation", "plaisir")
    lang = data.get("lang", "fr")


    textes_possession = {
        "fr": {

            "cave_personnelle": (
                "Vous possédez (ou envisagez de posséder) une cave personnelle. "
                "Un choix empreint d’authenticité, symbole d’un lien intime avec vos bouteilles. "
                "Pensez à privilégier une orientation nord ou nord-est pour éviter les variations thermiques, "
                "à maintenir une température stable autour de 12 °C et une hygrométrie proche de 70 %. "
                "Évitez la lumière directe, et assurez une ventilation douce pour garantir le vieillissement optimal de vos vins."
            ),

            "cave_externalisee": (
                "Vous avez opté pour une cave externalisée ou une garde professionnelle. "
                "Une solution pratique pour garantir des conditions de conservation idéales, sans contrainte logistique. "
                "Avant de choisir un prestataire, vérifiez la stabilité thermique, le contrôle hygrométrique, "
                "ainsi que les garanties en matière d’assurance et de traçabilité des bouteilles. "
                "Certaines caves proposent également des outils digitaux pour suivre vos stocks à distance."
            ),

            "fonds_investissement": (
                "Vous vous intéressez à des fonds ou plateformes d’investissement dans le vin. "
                "Nous attirons votre attention sur le fait que GrandcruX ne fournit pas de conseil en investissement. "
                "Toutefois, il est toujours pertinent de s’informer de manière éclairée : "
                "renseignez-vous sur la gouvernance du fonds, la sélection des crus, les frais de gestion et la liquidité du support. "
                "Le vin peut être perçu comme une classe d’actifs alternative, à la croisée du plaisir et du patrimoine tangible."
            ),

            "pas_encore": (
                "Vous ne possédez pas encore de vin mais souhaitez vous renseigner. "
                "C’est une excellente démarche ! Nos conseillers GrandcruX sont disponibles pour vous accompagner, "
                "que ce soit pour découvrir les fondamentaux de la conservation, comprendre le marché du vin ou simplement choisir vos premières bouteilles."
            ),

            "intro_motivation": (
                "Nous avons noté que vos motivations principales étaient les suivantes :"
            ),

            "plaisir": (
                "Le plaisir gustatif.\n\n"
                "Il s'agit là d'une approche qui incarne l’essence même du vin. "
                "Partager une bouteille, découvrir un millésime, vivre un instant de convivialité : "
                "le vin, avant tout, se savoure. "
                "Chez GrandcruX, nous croyons que le plaisir est la première forme d’investissement émotionnel dans le vin."
            ),

            "transmission": (
                "La transmission familiale.\n\n"
                "C’est le signe que vous vous posez les bonnes questions. "
                "Transmettre une cave, c’est transmettre une histoire, une mémoire et un goût. "
                "Pour aller plus loin sur ce sujet, nous vous invitons à consulter la deuxième partie du rapport, "
                "consacrée à la pérennisation et à la transmission du patrimoine viticole."
            ),

            "placement": (
                "Le placement à long terme.\n\n"
                "Une réflexion judicieuse. Sans fournir de conseils en rendement ou en performance, "
                "nous soulignons que le vin peut constituer un actif alternatif à horizon long, "
                "conjuguant rareté, plaisir et valeur émotionnelle. "
                "Un équilibre rare entre passion et patrimoine."
            ),

            "diversification": (
                "La diversification du patrimoine.\n\n"
                "Une approche avisée. Le vin peut s’envisager comme une composante complémentaire d’un patrimoine global, "
                "au même titre que les voitures de collection, les œuvres d’art ou les montres d’exception. "
                "Un choix à la fois esthétique, sensoriel et patrimonial."
            )
        },

        "en": {

            "cave_personnelle": (
                "You own (or wish to own) a personal wine cellar — a choice that reflects authenticity and passion. "
                "Ensure a stable temperature around 12 °C, humidity near 70%, and avoid direct light. "
                "A north or northeast orientation helps prevent temperature fluctuations, "
                "while gentle ventilation ensures your wines age in perfect harmony."
            ),

            "cave_externalisee": (
                "You rely on a professional or externalized wine storage service. "
                "A practical and secure solution offering ideal storage conditions without the burden of maintenance. "
                "Before choosing a provider, check for thermal stability, humidity control, "
                "insurance coverage, and traceability systems. "
                "Some also offer digital access to monitor your collection remotely."
            ),

            "fonds_investissement": (
                "You are interested in wine investment funds or platforms. "
                "Please note that GrandcruX does not provide investment advice. "
                "However, we encourage you to research carefully — look into fund governance, "
                "wine selection criteria, management fees, and liquidity. "
                "Wine can be viewed as an alternative asset class, bridging tangible heritage and sensory pleasure."
            ),

            "pas_encore": (
                "You do not yet own wine but wish to learn more. "
                "An excellent decision ! GrandcruX advisors are available to guide you through "
                "the fundamentals of storage, the wine market, and the selection of your first bottles."
            ),

            "intro_motivation": (
                "We have noted that your main motivations are as follows:"
            ),

            "plaisir": (
                "Pleasure.\n\n"
                "This approach embodies the very essence of wine. Sharing a bottle, discovering a vintage, "
                "enjoying a convivial moment — wine, above all, is meant to be savoured. "
                "At GrandcruX, we believe that pleasure is the first true emotional investment in wine."
            ),

            "transmission": (
                "Family transmission.\n\n"
                "It shows that you are asking the right questions. Passing on a cellar means passing on a story, a memory, and a taste. "
                "To explore this topic further, please refer to the second part of the report, "
                "dedicated to the preservation and transmission of wine heritage."
            ),

            "placement": (
                "Long-term investment.\n\n"
                "A thoughtful perspective. While we do not provide advice on performance, "
                "wine can be considered an alternative long-term asset combining rarity, pleasure, and emotional value. "
                "A delicate balance between passion and heritage."
            ),

            "diversification": (
                "Diversification.\n\n"
                "A wise approach. Wine can be seen as a complementary component of a diversified portfolio, "
                "alongside collectible cars, art, or fine watches. "
                "A refined blend of aesthetics, enjoyment, and tangible value."
            )
        },

        "nl": {

            "cave_personnelle": (
                "U bezit (of wilt bezitten) een persoonlijke wijnkelder. "
                "Een authentieke keuze die een nauwe band met uw flessen weerspiegelt. "
                "Zorg voor een stabiele temperatuur rond 12 °C, een vochtigheidsgraad van ongeveer 70 %, "
                "vermijd direct licht en voorzie een zachte ventilatie. "
                "Een noord- of noordoostgerichte kelder voorkomt temperatuurschommelingen en bevordert een ideale rijping."
            ),

            "cave_externalisee": (
                "U kiest voor een externe of professionele wijnopslag. "
                "Een praktische oplossing die optimale bewaaromstandigheden biedt zonder onderhoudszorgen. "
                "Controleer bij de keuze van een aanbieder de temperatuurstabiliteit, luchtvochtigheid, "
                "verzekering en traceerbaarheid. Sommige aanbieders bieden ook digitale toegang tot uw voorraad."
            ),

            "fonds_investissement": (
                "U toont interesse in wijnbeleggingsfondsen of -platformen. "
                "Let op: GrandcruX geeft geen beleggingsadvies. "
                "Wij raden aan om goed geïnformeerd te blijven — onderzoek de structuur van het fonds, "
                "de selectiecriteria, de beheerskosten en de liquiditeit. "
                "Wijn kan worden beschouwd als een alternatieve beleggingscategorie, "
                "op het kruispunt van plezier en tastbaar erfgoed."
            ),

            "pas_encore": (
                "U bezit nog geen wijn maar wilt zich informeren. "
                "Een uitstekende stap ! De adviseurs van GrandcruX begeleiden u graag "
                "bij de basisprincipes van wijnbewaring, de markt en de keuze van uw eerste flessen."
            ),

            "intro_motivation": (
                "Wij hebben vastgesteld dat uw belangrijkste motivaties de volgende zijn:"
            ),

            "plaisir": (
                "Smaakgenot.\n\n"
                "Dit is de ware essentie van wijn. Een fles delen, een jaargang ontdekken, genieten van gezelligheid — "
                "wijn draait om beleving. Bij GrandcruX beschouwen we genot als de eerste en belangrijkste emotionele investering in wijn."
            ),

            "transmission": (
                "Familiale overdracht.\n\n"
                "Dit toont dat u de juiste vragen stelt. Een wijnkelder doorgeven betekent een verhaal, een herinnering en een smaak delen. "
                "Voor meer informatie verwijzen wij naar het tweede deel van dit rapport, "
                "gewijd aan het behoud en de overdracht van wijnbezit."
            ),

            "placement": (
                "Langetermijnbelegging.\n\n"
                "Een doordachte keuze. Hoewel wij geen rendementadvies geven, kan wijn worden beschouwd als een alternatief langetermijnactief "
                "dat zeldzaamheid, plezier en emotionele waarde combineert. "
                "Een subtiel evenwicht tussen passie en erfgoed."
            ),

            "diversification": (
                "Diversificatie.\n\n"
                "Een verstandige aanpak. Wijn kan deel uitmaken van een evenwichtige vermogensverdeling, "
                "naast kunst, oldtimers of luxe horloges. "
                "Een unieke mix van esthetiek, beleving en waarde."
            )
        }
    }

    texte_possession = textes_possession.get(lang, textes_possession["fr"]).get(
        forme_possession, textes_possession["fr"]["pas_encore"]
    )

    texte_intro_motivation = textes_possession.get(lang, textes_possession["fr"])["intro_motivation"]

    # Texte motivation principale
    texte_motivation = textes_possession.get(lang, textes_possession["fr"]).get(
        motivation, textes_possession["fr"]["plaisir"]
    )

    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 8, txt=clean_text(texte_possession), align="L")
    pdf.ln(6)

    pdf.set_font("Helvetica", "I", size=12)
    pdf.multi_cell(0, 8, txt=clean_text(texte_intro_motivation), align="L")
    pdf.ln(4)

    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 8, txt=clean_text(texte_motivation), align="L")
    pdf.ln(10)

    bouteille_path = "static/bouteille.jpg"
    if os.path.exists(bouteille_path):
        # On dessine la bouteille légèrement à gauche du texte
        y_pos = pdf.get_y()
        pdf.image(bouteille_path, x=35, y=y_pos + 1, w=8)
        text_x = 48
    else:
        text_x = 43

    # === Titre "Votre appétence au risque" (multilingue) ===
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(106, 27, 27)  # bordeaux #6a1b1b
    pdf.set_x(text_x)

    lang = data.get("lang", "fr")

    titre_risque = {
        "fr": "Votre appétence au risque",
        "en": "Your Risk Appetite",
        "nl": "Uw risicobereidheid"
    }

    pdf.cell(0, 10, titre_risque.get(lang, titre_risque["fr"]), ln=True, align="L")
    pdf.ln(6)

    # === Corps de texte (noir) ===
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", size=12)

    risque = data.get("risque", "modere")
    lang = data.get("lang", "fr")

    textes_risque = {
        "fr": {
            "intro": (
                "Nous avons noté votre appétence au risque suivante : "
            ),

            "tres_faible": (
                "Risque très faible — vous privilégiez la sécurité.\n\n"
                "Dans ce cas, le vin peut être perçu avant tout comme un actif plaisir, "
                "dont le 'rendement' principal réside dans le plaisir de dégustation et la valorisation patrimoniale émotionnelle. "
                "Il n’y a ici aucun risque ou un risque très contenu, "
                "puisque le vin reste un bien tangible qui peut être conservé, transmis… ou dégusté. "
                "Nous rappelons que GrandcruX ne fournit pas de conseils en investissement, "
                "et que cette approche s’inscrit avant tout dans une logique de sécurité et de passion raisonnée."
            ),

            "modere": (
                "Risque modéré — un équilibre entre plaisir et rendement.\n\n"
                "Cette approche traduit une vision équilibrée : l’envie de concilier plaisir et potentiel de valorisation. "
                "Il est effectivement possible d’obtenir des rendements modérés sur certaines cuvées recherchées, "
                "mais toujours dans une optique de long terme et sans garantie. "
                "Nous ne sommes pas conseillers en investissement, et ne formulons pas de recommandations financières. "
                "Le vin reste un placement alternatif, où la dimension plaisir et patrimoine prime sur la recherche de performance."
            ),

            "eleve": (
                "Risque élevé — la recherche de performance.\n\n"
                "Certains acteurs spécialisés proposent des placements à haut risque dans le vin, "
                "souvent liés à la spéculation sur des millésimes rares ou des volumes limités. "
                "Cependant, la recherche de performance n’est pas, à notre connaissance, "
                "l’élément qui caractérise le plus l’investissement dans le vin. "
                "Notre démarche n’a pas vocation à offrir des conseils en investissement ni à viser le rendement à tout prix. "
                "Le vin s’envisage avant tout comme un actif alternatif, mêlant passion, culture et patrimoine tangible."
            )
        },

        "en": {
            "intro": (
                "We have noted the following risk appetite : "
            ),

            "tres_faible": (
                "Very low risk — you prioritise safety.\n\n"
                "In this case, wine can be seen primarily as a pleasure asset, "
                "whose main 'return' lies in enjoyment, heritage and tangible value. "
                "There is virtually no risk, as wine remains a consumable and collectible good. "
                "We remind you that GrandcruX does not provide investment advice; "
                "this approach is above all one of prudence, stability and pleasure."
            ),

            "modere": (
                "Moderate risk — a balance between pleasure and return.\n\n"
                "This balanced perspective reflects an interest in both enjoyment and potential appreciation. "
                "It is possible to achieve moderate returns on certain sought-after vintages, "
                "though always over the long term and without any guarantees. "
                "We are not investment advisers and do not issue financial recommendations. "
                "Wine remains an alternative asset class, where passion and culture take precedence over performance."
            ),

            "eleve": (
                "High risk — a search for performance.\n\n"
                "Some specialised platforms offer high-risk investments in fine wine, "
                "often linked to speculation on rare vintages or limited productions. "
                "However, the pursuit of performance is not, to our knowledge, "
                "what best characterises wine investment. "
                "GrandcruX does not provide investment advice and does not promote a performance-driven approach. "
                "Wine should be viewed primarily as an alternative, tangible and cultural asset."
            )
        },

        "nl": {
            "intro": (
                "Wij hebben uw risicobereidheid vastgesteld : "
            ),

            "tres_faible": (
                "Zeer laag risico — u geeft de voorkeur aan veiligheid.\n\n"
                "In dit geval kan wijn worden beschouwd als een plezierbezit, "
                "waarvan het belangrijkste 'rendement' ligt in genot en erfgoedwaarde. "
                "Er is nauwelijks risico, aangezien wijn een tastbaar goed blijft dat men kan bewaren, doorgeven of consumeren. "
                "Wij herinneren eraan dat GrandcruX geen beleggingsadvies verstrekt "
                "en dat deze benadering vooral draait om veiligheid en passie."
            ),

            "modere": (
                "Gemiddeld risico — een evenwicht tussen plezier en rendement.\n\n"
                "Deze houding getuigt van een evenwichtige visie: de wens om plezier te combineren met mogelijke waardestijging. "
                "Op bepaalde gezochte jaargangen kan een gematigd rendement worden gerealiseerd, "
                "maar altijd op lange termijn en zonder garantie. "
                "Wij zijn geen beleggingsadviseurs en geven geen financieel advies. "
                "Wijn blijft een alternatief actief, waarbij beleving en erfgoed belangrijker zijn dan pure prestatie."
            ),

            "eleve": (
                "Hoog risico — op zoek naar prestaties.\n\n"
                "Sommige gespecialiseerde spelers bieden beleggingen met hoog risico aan in wijn, "
                "vaak gericht op speculatie met zeldzame jaargangen of beperkte producties. "
                "De zoektocht naar prestaties is echter, voor zover wij weten, "
                "niet wat het meest typerend is voor beleggen in wijn. "
                "GrandcruX verstrekt geen beleggingsadvies en richt zich niet op rendement tegen elke prijs. "
                "Wijn moet worden gezien als een alternatief, tastbaar en cultureel actief."
            )
        }
    }


    texte_intro = textes_risque.get(lang, textes_risque["fr"])["intro"]
    texte_risque = textes_risque.get(lang, textes_risque["fr"]).get(risque, textes_risque["fr"]["modere"])

    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 8, txt=clean_text(texte_intro), align="L")
    pdf.ln(6)

    pdf.multi_cell(0, 8, txt=clean_text(texte_risque), align="L")
    pdf.ln(10)

    pdf.add_page()
    canevas_path = "static/canevas.jpg"
    if os.path.exists(canevas_path):
        pdf.image(canevas_path, x=0, y=0, w=210, h=297)

    # === Titre "Le vin comme outil de transmission" (multilingue) ===
    pdf.set_font("Helvetica", style="B", size=22)
    pdf.set_text_color(128, 0, 32)  # rouge bordeaux
    pdf.ln(17)

    lang = data.get("lang", "fr")

    titre_transmission = {
        "fr": "Le vin comme outil de transmission",
        "en": "Wine as a Tool for Transmission",
        "nl": "Wijn als instrument voor overdracht"
    }

    pdf.cell(0, 20, titre_transmission.get(lang, titre_transmission["fr"]), ln=True, align="C")

    # === Ligne décorative sous le titre ===
    pdf.set_draw_color(128, 0, 32)
    pdf.set_line_width(0.8)
    page_width = pdf.w
    margin = 60
    y_line = pdf.get_y()
    pdf.line(margin, y_line, page_width - margin, y_line)
    pdf.ln(15)

    # === Corps de texte (noir) ===
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", size=12)

    # --- Données utilisateur ---
    lang = data.get("lang", "fr")
    enfants = data.get("enfants", "non")
    nombre_enfants_str = data.get("nombre_enfants", "").strip()
    nombre_enfants = int(nombre_enfants_str) if nombre_enfants_str.isdigit() else 0

    # === Textes multilingues ===
    textes_transmission = {
        "fr": {
            "intro": (
                "Avant toute chose, il existe des règles légales encadrant la transmission du patrimoine. "
                "Le vin, bien qu’il évoque la passion et la culture, est considéré en droit comme un bien meuble. "
                "À ce titre, il est, tout comme les biens immeubles, susceptible d’imposition dans le cadre des droits de succession.\n\n"
                "Retenez avant tout ceci : en Belgique, les droits de succession sont régionalisés. "
                "Les règles d’imposition diffèrent selon que vous résidez en Région wallonne, en Région flamande ou encore à Bruxelles-Capitale."
            ),

            "enfants_oui": (
                "Nous avons noté que vous aviez des enfants.\n\n"
                "La présence d’enfants influe directement sur la répartition successorale. "
                "En effet, le Code civil prévoit une réserve héréditaire légale pour chaque enfant. "
                "Celle-ci garantit qu’une partie de votre patrimoine — appelée 'masse successorale' ou 'masse fictive' — "
                "leur reviendra nécessairement. Cette masse correspond à la somme de vos biens au moment du décès, "
                "diminuée de vos dettes et augmentée des donations effectuées de votre vivant.\n\n"
                "Ainsi, la moitié de cette masse est dite 'quotité disponible' (dont vous pouvez librement disposer), "
                "et l’autre moitié constitue la 'réserve' partagée entre vos enfants au prorata.\n\n"
                "Ces dispositions assurent la protection familiale tout en laissant une marge de liberté patrimoniale. "
                "Nous verrons plus bas comment ces règles peuvent s’articuler avec la transmission de votre cave et de vos vins."
            ),

            "enfants_non": (
                "Nous avons noté que vous n’aviez pas d’enfants.\n\n"
                "Dans ce cas, la loi désigne vos héritiers selon le principe des ordres et des degrés : "
                "vos parents, frères, soeurs, oncles et tantes peuvent hériter directement. "
                "Cependant, en l’absence de descendants, les droits de succession peuvent s’avérer élevés, "
                "notamment lorsqu’ils s’appliquent à des collatéraux.\n\n"
                "Il peut être utile d’y réfléchir à l’avance, afin de préserver la valeur symbolique et financière de votre cave. "
                "Nous verrons plus bas comment certaines dispositions patrimoniales peuvent optimiser cette transmission."
            ),

            "analyse_intro": (
                "À côté des taxations, il existe heureusement des règles de protection mises en place par la loi.\n\n"
                "Ainsi, une réserve légale est prévue par enfant. Très concrètement, cela signifie qu’une partie de la masse successorale "
                "(également appelée 'masse fictive', car elle additionne fictivement les biens donnés de votre vivant) "
                "est réservée à vos enfants.\n\n"
                "Cette masse se partage entre deux moitiés : la quotité disponible (librement transmissible) et la réserve (protégée pour vos héritiers)."
            ),

            "analyse_suite": (
                "Voici donc comment se répartit la réserve de vos enfants sur la moitié de la masse successorale. "
                "Ceci illustre, de manière simplifiée, ce que la loi leur garantit en cas de succession.\n\n"
                "Nous reprendrons ces règles plus bas dans le cas particulier du vin."
            )
        },

        "en": {
            "intro": (
                "First and foremost, inheritance and transfer of assets are governed by specific legal rules. "
                "Wine, although associated with culture and passion, is legally considered a movable asset. "
                "As such, it may be subject to inheritance taxation, much like real estate.\n\n"
                "Keep in mind that in Belgium, inheritance tax is a regional matter. "
                "Taxation rules differ between the Walloon Region, the Flemish Region, and the Brussels-Capital Region."
            ),

            "enfants_oui": (
                "We have noted that you have children.\n\n"
                "The presence of children directly affects inheritance rules. "
                "Belgian civil law provides a legal hereditary reserve for each child — "
                "a portion of your total estate (the so-called 'fictitious estate mass') that cannot be deprived from them. "
                "This mass includes all assets owned at death, minus debts, and adds back any donations made during your lifetime.\n\n"
                "Half of this mass is freely disposable ('available share'), "
                "while the other half forms the children's reserve, divided equally among them.\n\n"
                "This ensures family protection while maintaining flexibility in estate planning. "
                "We will later see how these principles apply specifically to wine and cellar inheritance."
            ),

            "enfants_non": (
                "We have noted that you do not have children.\n\n"
                "In this situation, Belgian succession law designates heirs according to the legal orders of kinship: "
                "your parents, siblings, uncles, and aunts may inherit directly. "
                "However, without descendants, inheritance taxes can be particularly high — "
                "especially for collateral heirs.\n\n"
                "It may therefore be wise to anticipate this to preserve the symbolic and financial value of your wine collection. "
                "We will later explore how estate tools can optimise this transmission."
            ),

            "analyse_intro": (
                "Alongside taxation, Belgian law provides protective inheritance mechanisms.\n\n"
                "A legal reserve exists for each child. In practice, this means that part of your total estate "
                "(the 'fictitious mass', which includes all gifted and current assets) "
                "is guaranteed to your heirs.\n\n"
                "Half of the estate is freely disposable, and the other half is reserved proportionally for your children."
            ),

            "analyse_suite": (
                "Below is a simplified illustration of how this hereditary reserve is distributed among your children. "
                "It represents the portion of your estate to which each child is legally entitled.\n\n"
                "We will see these rules further below in the specific case of wine."
            )
        },

        "nl": {
            "intro": (
                "Voordat men aan overdracht denkt, is het belangrijk te weten dat de erfopvolging wettelijk geregeld is. "
                "Wijn, hoe gepassioneerd en cultureel ook, wordt juridisch beschouwd als een roerend goed. "
                "Net als onroerend goed kan het dus worden belast in het kader van de successierechten.\n\n"
                "Onthoud vooral dit: in België zijn de successierechten geregionaliseerd. "
                "De fiscale regels verschillen naargelang u woont in het Waalse Gewest, het Vlaamse Gewest of het Brussels Hoofdstedelijk Gewest."
            ),

            "enfants_oui": (
                "Wij hebben genoteerd dat u kinderen heeft.\n\n"
                "De aanwezigheid van kinderen heeft een directe invloed op de verdeling van de nalatenschap. "
                "Volgens het Burgerlijk Wetboek bestaat er een wettelijke erfrechtelijke reserve voor elk kind. "
                "Een deel van uw vermogen — de zogenaamde 'fictieve nalatenschapsmassa' — "
                "moet dus verplicht aan hen worden toebedeeld.\n\n"
                "De helft van deze massa is vrij beschikbaar ('beschikbaar deel'), "
                "de andere helft vormt de 'reserve' die gelijk verdeeld wordt onder uw kinderen.\n\n"
                "Deze regeling waarborgt bescherming van het gezin en biedt tegelijk enige vrijheid. "
                "Verderop bekijken we hoe deze regels van toepassing zijn op wijn en wijnkelders."
            ),

            "enfants_non": (
                "Wij hebben genoteerd dat u geen kinderen heeft.\n\n"
                "In dat geval bepaalt de wet uw erfgenamen volgens orde en graad: "
                "ouders, broers, zussen, ooms en tantes kunnen rechtstreeks erven. "
                "Bij afwezigheid van afstammelingen kunnen de successierechten echter hoog oplopen, "
                "vooral bij zijverwanten.\n\n"
                "Het is dus verstandig om hier vooraf bij stil te staan, "
                "om de symbolische en financiële waarde van uw wijncollectie te behouden. "
                "Verderop tonen we hoe bepaalde regelingen de overdracht kunnen optimaliseren."
            ),

            "analyse_intro": (
                "Naast de belasting bestaan er beschermingsmechanismen voorzien door de wet.\n\n"
                "Er is een wettelijke reserve per kind. Dit betekent dat een deel van de nalatenschapsmassa "
                "(ook wel 'fictieve massa' genoemd, omdat het schenkingen uit het verleden meerekent) "
                "verplicht aan uw kinderen wordt toegewezen.\n\n"
                "De helft van deze massa is vrij beschikbaar en de andere helft wordt gelijk verdeeld onder uw kinderen."
            ),

            "analyse_suite": (
                "Hieronder ziet u een vereenvoudigde voorstelling van de verdeling van deze reserve. "
                "Dit geeft weer welk deel van de nalatenschap wettelijk aan elk kind toekomt.\n\n"
                "We zullen deze regels verderop opnieuw bekijken in het specifieke geval van wijn."
            )
        }
    }

    # === Sélection des textes selon la situation ===
    texte_intro = textes_transmission.get(lang, textes_transmission["fr"])["intro"]
    texte_transmission = (
        textes_transmission.get(lang, textes_transmission["fr"])["enfants_oui"]
        if enfants == "oui"
        else textes_transmission.get(lang, textes_transmission["fr"])["enfants_non"]
    )

    pdf.multi_cell(0, 8, txt=clean_text(texte_intro), align="L")
    pdf.ln(6)
    pdf.multi_cell(0, 8, txt=clean_text(texte_transmission), align="L")
    pdf.ln(10)

    # === Si enfants, on affiche l’analyse et le diagramme ===
    if enfants == "oui" and nombre_enfants > 0:
        pdf.add_page()
        canevas_path = "static/canevas.jpg"
        if os.path.exists(canevas_path):
            pdf.image(canevas_path, x=0, y=0, w=210, h=297)

        bouteille_path = "static/bouteille.jpg"
        pdf.set_y(30)
        if os.path.exists(bouteille_path):
            y_pos = pdf.get_y()
            pdf.image(bouteille_path, x=35, y=y_pos + 1, w=8)
            text_x = 48
        else:
            text_x = 43

        # === Titre "La réserve légale et la quotité disponible" (multilingue) ===
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(106, 27, 27)  # bordeaux
        pdf.set_x(text_x)

        lang = data.get("lang", "fr")

        titre_reserve = {
            "fr": "La réserve légale et la quotité disponible",
            "en": "The Legal Reserve and the Disposable Portion",
            "nl": "De wettelijke reserve en het beschikbare deel"
        }

        pdf.cell(0, 10, titre_reserve.get(lang, titre_reserve["fr"]), ln=True, align="L")
        pdf.ln(10)

        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", size=12)

        analyse_intro = textes_transmission.get(lang, textes_transmission["fr"])["analyse_intro"]
        analyse_suite = textes_transmission.get(lang, textes_transmission["fr"])["analyse_suite"]

        pdf.multi_cell(0, 8, txt=clean_text(analyse_intro), align="L")
        pdf.ln(6)
        # === Phrase multilingue sur le nombre d’enfants ===
        if lang == "fr":
            pdf.cell(0, 8, f"Vous avez {nombre_enfants} enfant{'s' if nombre_enfants != 1 else ''}.", ln=True)
        elif lang == "en":
            pdf.cell(0, 8, f"You have {nombre_enfants} child{'ren' if nombre_enfants != 1 else ''}.", ln=True)
        elif lang == "nl":
            pdf.cell(0, 8, f"U heeft {nombre_enfants} kind{'eren' if nombre_enfants != 1 else ''}.", ln=True)
        else:
            pdf.cell(0, 8, f"Vous avez {nombre_enfants} enfant{'s' if nombre_enfants != 1 else ''}.", ln=True)

        # --- Diagramme de répartition ---
        labels = ['Quotité disponible']
        sizes = [50]
        colors = ['#C29E75']  # beige doré (chêne clair)

        part_reserve = 50 / nombre_enfants
        for i in range(1, nombre_enfants + 1):
            labels.append(f"Réserve enfant {i}")
            sizes.append(part_reserve)
            # Couleurs bordeaux / vin
            couleurs_vin = ['#6A1B1B', '#7B2D26', '#8C3F32', '#9E5040', '#B5651D']
            colors.append(couleurs_vin[i % len(couleurs_vin)])

        fig, ax = plt.subplots()
        ax.pie(
            sizes, labels=labels, autopct='%1.1f%%', colors=colors,
            startangle=90, wedgeprops={'edgecolor': 'white', 'linewidth': 2}
        )
        ax.axis('equal')
        plt.title("Masse successorale (ou 'fictive')")
        plt.savefig("diagramme_successoral.png", bbox_inches='tight')
        plt.close(fig)

        image_width = 100
        pdf_width = 210
        x_position = (pdf_width - image_width) / 2
        pdf.image("diagramme_successoral.png", x=x_position, y=None, w=image_width)
        os.remove("diagramme_successoral.png")

        pdf.ln(10)
        pdf.multi_cell(0, 8, txt=clean_text(analyse_suite), align="L")
        pdf.ln(10)

    pdf.add_page()
    canevas_path = "static/canevas.jpg"
    if os.path.exists(canevas_path):
        pdf.image(canevas_path, x=0, y=0, w=210, h=297)

    bouteille_path = "static/bouteille.jpg"
    pdf.set_y(30)
    if os.path.exists(bouteille_path):
        # On dessine la bouteille légèrement à gauche du texte
        y_pos = pdf.get_y()
        pdf.image(bouteille_path, x=55, y=y_pos + 1, w=8)
        text_x = 67
    else:
        text_x = 60

    # === Titre "Le régime matrimonial" (multilingue) ===
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(106, 27, 27)  # bordeaux #6a1b1b
    pdf.set_x(text_x)

    lang = data.get("lang", "fr")

    titre_regime = {
        "fr": "Le régime matrimonial",
        "en": "The Matrimonial Regime",
        "nl": "Het huwelijksstelsel"
    }

    pdf.cell(0, 10, titre_regime.get(lang, titre_regime["fr"]), ln=True, align="L")
    pdf.ln(6)

    # === Corps de texte (noir) ===
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", size=12)

    # --- Données utilisateur ---
    lang = data.get("lang", "fr")
    mariage = data.get("mariage", "non")
    regime = data.get("regime", "")

    # === Textes multilingues ===
    textes_matrimonial = {
        "fr": {
            "intro": (
                "Avant d’aborder la succession, il faut d’abord liquider le régime matrimonial lorsqu’il en existe un. "
                "Ce principe est essentiel : il permet de déterminer ce qui appartient à chacun des époux avant toute répartition successorale.\n\n"
                "Lorsque le couple a des enfants, la succession associe souvent les notions d’usufruit (au profit du conjoint survivant) "
                "et de nue-propriété (au profit des enfants). Cette structure permet à la fois une protection du conjoint et une optimisation fiscale. "
                "Nous n’entrerons pas ici dans le détail technique de ces règles. "
                "Sachez que pour le vin, une convention de quasi-usufruit (sous seing privé ou chez le notaire) pourrait être envisagée."

            ),

            "non": (
                "Vous n’êtes pas marié(e).\n\n"
                "Dans ce cas, vous êtes soit célibataire, soit en cohabitation de fait, soit en cohabitation légale.\n\n"
                "- En cas de **cohabitation de fait**, votre partenaire ne reçoit rien par succession légale. "
                "Si vous souhaitez qu’il ou elle hérite de votre cave ou de la valeur de vos vins, "
                "il est nécessaire de le prévoir expressément par testament.\n\n"
                "- En cas de **cohabitation légale**, vous êtes assimilé à un régime de séparation des biens : "
                "vos patrimoines restent distincts, chacun conservant la propriété de ses biens, y compris vos vins et bouteilles personnelles.\n\n"
                "Dans les deux cas, la prévoyance et la clarté juridique sont des clés pour préserver la transmission harmonieuse de votre patrimoine viticole."
            ),

            "communautelegale": (
                "Vous êtes marié(e) sous le régime de la **communauté légale**.\n\n"
                "Dans ce régime, les biens acquis avant le mariage restent propres, "
                "tandis que ceux acquis pendant le mariage (y compris les revenus) deviennent communs.\n\n"
                "Vos vins achetés avant le mariage restent donc votre propriété personnelle, "
                "tandis que les bouteilles acquises durant le mariage appartiennent à la communauté.\n\n"
                "Ce régime assure un équilibre entre autonomie et partage. "
                "Il offre également certaines protections fiscales et successorales entre époux."
            ),

            "separationbien": (
                "Vous êtes marié(e) sous le régime de la **séparation de biens**.\n\n"
                "Chaque époux conserve ici son patrimoine propre. "
                "Il n’existe pas de masse commune : chacun reste propriétaire exclusif des biens qu’il acquiert.\n\n"
                "Vos vins sont donc strictement rattachés à votre patrimoine personnel, "
                "sauf mention contraire (donation, achat commun, etc.).\n\n"
                "Ce régime offre une grande indépendance patrimoniale, "
                "mais peut nécessiter une attention accrue à la protection du conjoint survivant.\n\n"
            ),

            "communauteuniverselle": (
                "Vous êtes marié(e) sous le régime de la **communauté universelle**.\n\n"
                "Tous les biens, qu’ils aient été acquis avant ou pendant le mariage, "
                "sont mis en commun, sauf clauses particulières dans le contrat.\n\n"
                "Les vins acquis avant ou après le mariage appartiennent donc à la communauté. "
                "En cas de décès, le conjoint survivant conserve une part significative du patrimoine, "
                "ce qui peut favoriser la stabilité successorale mais limiter la part des enfants.\n\n"
                "Ce régime est souvent choisi dans une logique de protection maximale du couple."
            )
        },

        "en": {
            "intro": (
                "Before addressing inheritance, it is necessary to settle the matrimonial regime when one exists. "
                "This determines what belongs to each spouse before any estate division.\n\n"
                "When children are involved, inheritance usually combines **usufruct (for the surviving spouse)** "
                "and **bare ownership (for the children)** — a structure that offers both protection and tax efficiency. "
                "We will not delve into the legal mechanisms."
                "Please note that for the wine, a quasi-usufruct agreement (either under private signature or through a notary) "
                "could be considered."
            ),

            "non": (
                "You are not married.\n\n"
                "This means you are either single, in de facto cohabitation, or in legal cohabitation.\n\n"
                "- In the case of **de facto cohabitation**, your partner has no inheritance rights by default. "
                "If you wish for them to inherit your wine cellar or the value of your wines, "
                "this must be explicitly provided for in a will.\n\n"
                "- In **legal cohabitation**, you are considered under a separation of property regime — "
                "each partner retains ownership of their own assets, including their wines.\n\n"
                "In both cases, careful estate planning helps preserve the symbolic and financial value of your wine collection."
            ),

            "communautelegale": (
                "You are married under the **legal community regime**.\n\n"
                "Assets acquired before marriage remain personal, "
                "while those acquired during marriage (including income) are jointly owned.\n\n"
                "Wines purchased before marriage remain your property, "
                "while those acquired afterward belong to the community.\n\n"
                "This regime provides balance and mutual protection, "
                "and offers certain tax and inheritance benefits between spouses."
            ),

            "separationbien": (
                "You are married under the **separation of property** regime.\n\n"
                "Each spouse maintains their own estate — there is no shared community property.\n\n"
                "Your wines are therefore part of your personal assets, "
                "unless otherwise stipulated (e.g., joint purchase or donation).\n\n"
                "This regime grants financial independence, "
                "but may require additional arrangements to protect the surviving spouse.\n\n"
            ),

            "communauteuniverselle": (
                "You are married under the **universal community** regime.\n\n"
                "All assets — whether acquired before or after marriage — "
                "are considered joint property, unless exceptions are defined in the marriage contract.\n\n"
                "Wines purchased at any time are therefore part of the shared estate. "
                "In the event of death, the surviving spouse retains a substantial portion of the assets, "
                "which enhances protection but reduces the share available to heirs.\n\n"
                "This regime is often chosen to ensure full protection of the couple."
            )
        },

        "nl": {
            "intro": (
                "Voordat men aan de nalatenschap denkt, moet eerst het huwelijksvermogensstelsel worden vereffend indien dit bestaat. "
                "Dit bepaalt wat aan elke echtgenoot toebehoort vóór de verdeling van de erfenis.\n\n"
                "Wanneer er kinderen zijn, wordt vaak gewerkt met **vruchtgebruik (voor de langstlevende echtgenoot)** "
                "en **blote eigendom (voor de kinderen)** — een structuur die bescherming en fiscale optimalisatie combineert. "
                "We gaan niet in op de technische details."
                "Weet dat voor de wijn een quasi-vruchtgebruikovereenkomst (onderhands of via een notaris) kan worden "
                "overwogen."

            ),

            "non": (
                "U bent niet gehuwd.\n\n"
                "Dit betekent dat u vrijgezel bent, feitelijk samenwoont of wettelijk samenwoont.\n\n"
                "- Bij **feitelijke samenwoning** erft uw partner niets automatisch. "
                "Wilt u dat hij of zij uw wijncollectie of de waarde ervan erft, dan moet u dit vastleggen in een testament.\n\n"
                "- Bij **wettelijke samenwoning** geldt een **scheiding van goederen** : "
                "ieder behoudt zijn eigen vermogen, inclusief zijn wijnbezit.\n\n"
                "In beide gevallen is het verstandig om vooruit te plannen om de waarde van uw wijncollectie te behouden."
            ),

            "communautelegale": (
                "U bent gehuwd onder het **wettelijk stelsel**.\n\n"
                "Goederen van vóór het huwelijk blijven persoonlijk, "
                "terwijl goederen die tijdens het huwelijk worden verworven, gemeenschappelijk worden.\n\n"
                "Wijnen die vóór het huwelijk zijn gekocht, blijven dus persoonlijk, "
                "terwijl wijnen die daarna zijn verworven, gemeenschappelijk zijn.\n\n"
                "Dit stelsel biedt een evenwicht tussen autonomie en solidariteit en voorziet in bescherming tussen echtgenoten."
            ),

            "separationbien": (
                "U bent gehuwd onder het **stelsel van scheiding van goederen**.\n\n"
                "Elke echtgenoot behoudt hier zijn eigen vermogen : er is geen gemeenschappelijk vermogen.\n\n"
                "Uw wijnen behoren dus uitsluitend tot uw persoonlijke vermogen, "
                "tenzij anders overeengekomen (bijvoorbeeld gemeenschappelijke aankoop of schenking).\n\n"
                "Dit stelsel waarborgt financiële onafhankelijkheid, "
                "maar kan aanvullende bescherming voor de langstlevende vereisen.\n\n"
            ),

            "communauteuniverselle": (
                "U bent gehuwd onder het **stelsel van algehele gemeenschap**.\n\n"
                "Alle goederen, zowel van vóór als van na het huwelijk, "
                "worden gemeenschappelijk eigendom, tenzij het contract anders bepaalt.\n\n"
                "Uw wijnbezit behoort dus volledig tot de gemeenschap. "
                "Bij overlijden behoudt de langstlevende echtgenoot een groot deel van het vermogen, "
                "wat bescherming biedt maar het erfdeel van de kinderen verkleint.\n\n"
                "Dit stelsel wordt vaak gekozen om de onderlinge bescherming te versterken."
            )
        }
    }

    # === Sélection du texte ===
    texte_intro = textes_matrimonial.get(lang, textes_matrimonial["fr"])["intro"]
    pdf.multi_cell(0, 8, txt=clean_text(texte_intro), align="L")
    pdf.ln(6)

    if mariage == "non":
        texte_mariage = textes_matrimonial.get(lang, textes_matrimonial["fr"])["non"]
        pdf.multi_cell(0, 8, txt=clean_text(texte_mariage), align="L")
        pdf.ln(10)
    else:
        texte_regime = textes_matrimonial.get(lang, textes_matrimonial["fr"]).get(regime, "")
        if texte_regime:
            pdf.multi_cell(0, 8, txt=clean_text(texte_regime), align="L")
            pdf.ln(8)

            # --- Illustration selon le régime ---
            if regime == "communautelegale":
                image_path = "static/regime_legal.jpg"
            elif regime == "separationbien":
                image_path = "static/separation_biens.jpg"
            elif regime == "communauteuniverselle":
                image_path = "static/communaute_universelle.jpg"
            else:
                image_path = ""

            if image_path and os.path.exists(image_path):
                image_width = 100
                pdf_width = 210
                x_position = (pdf_width - image_width) / 2
                pdf.image(image_path, x=x_position, y=None, w=image_width)
                pdf.ln(10)

    pdf.add_page()
    canevas_path = "static/canevas.jpg"
    if os.path.exists(canevas_path):
        pdf.image(canevas_path, x=0, y=0, w=210, h=297)

    bouteille_path = "static/bouteille.jpg"
    pdf.set_y(30)
    if os.path.exists(bouteille_path):
        # On dessine la bouteille légèrement à gauche du texte
        y_pos = pdf.get_y()
        pdf.image(bouteille_path, x=55, y=y_pos + 1, w=8)
        text_x = 67
    else:
        text_x = 60

    # === Titre "Modes alternatifs d’optimisation" (multilingue) ===
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(106, 27, 27)  # bordeaux #6a1b1b
    pdf.set_x(text_x)

    lang = data.get("lang", "fr")

    titre_optimisation = {
        "fr": "Modes alternatifs d'optimisation",
        "en": "Alternative Ways of Optimisation",
        "nl": "Alternatieve optimalisatiemethoden"
    }

    pdf.cell(0, 10, titre_optimisation.get(lang, titre_optimisation["fr"]), ln=True, align="L")
    pdf.ln(6)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", size=12)

    # --- Données utilisateur ---
    lang = data.get("lang", "fr")
    societe = data.get("societe", "non")
    type_societe = data.get("type_societe", "").strip()

    # === Textes multilingues ===
    textes_societe = {
        "fr": {
            "intro": (
                "Outre la transmission familiale classique, certaines formes de détention patrimoniale peuvent s’effectuer "
                "par le biais d’une société. Cela peut offrir des voies d’optimisation ou de planification, "
                "notamment lorsqu’il s’agit d’actifs tangibles comme le vin.\n\n"
                "Si vous disposez d’une société, plusieurs leviers légaux belges peuvent être abordés avec votre comptable : "
                "le versement de dividendes, la constitution de réserves de liquidation, ou encore le régime fiscal VVPRbis. "
                "Ces mécanismes peuvent, dans certains cas, contribuer à une transmission progressive ou fiscalement efficiente.\n\n"
                "Nous vous invitons à aborder ces questions avec votre professionnel de confiance afin d’en évaluer la pertinence dans votre situation."
            ),

            "type": (
                "Nous notons que vous disposez de la société suivante : {type_societe}."
            ),

            "non": (
                "Vous n’avez pas de société déclarée. Dans ce cas, la transmission de votre patrimoine viticole s’effectuera principalement "
                "à titre personnel, dans le cadre du droit successoral classique."
            )
        },

        "en": {
            "intro": (
                "Beyond traditional family succession, certain assets — such as wine — can also be held and transmitted through a company. "
                "This structure may open up opportunities for optimisation or long-term planning.\n\n"
                "If you own a company, your accountant may advise you on mechanisms recognised under Belgian law such as "
                "dividend distribution, liquidation reserves, or the VVPRbis regime. "
                "These can, in some cases, support gradual or tax-efficient transmission.\n\n"
                "We encourage you to discuss these aspects with your trusted advisor to assess what may apply to your situation."
            ),

            "type": (
                "We note that you have indicated the following company type: {type_societe}."
            ),

            "non": (
                "You have indicated that you do not own a company. "
                "In this case, the transmission of your wine assets will follow the general principles of personal inheritance law."
            )
        },

        "nl": {
            "intro": (
                "Naast de klassieke familiale overdracht kan een deel van het vermogen — zoals wijn — ook via een vennootschap worden beheerd. "
                "Dit kan mogelijkheden bieden voor optimalisatie en langetermijnplanning.\n\n"
                "Indien u een vennootschap bezit, kan uw boekhouder u informeren over mechanismen die in België bestaan, "
                "zoals dividenduitkeringen, liquidatiereserves of het VVPRbis-stelsel. "
                "Deze instrumenten kunnen in bepaalde gevallen bijdragen tot een geleidelijke of fiscaal gunstige overdracht.\n\n"
                "Bespreek deze opties gerust met uw vertrouwenspersoon om te bepalen wat voor u relevant is."
            ),

            "type": (
                "Wij merken op dat u de volgende vennootschap hebt opgegeven: {type_societe}."
            ),

            "non": (
                "U hebt geen vennootschap vermeld. "
                "In dat geval zal de overdracht van uw wijnbezit hoofdzakelijk plaatsvinden via de gewone erfregels."
            )
        }
    }

    # === Sélection du texte ===
    texte_intro = textes_societe.get(lang, textes_societe["fr"])["intro"]
    pdf.multi_cell(0, 8, txt=clean_text(texte_intro), align="L")
    pdf.ln(6)

    if societe == "oui":
        if type_societe:
            texte_type = textes_societe.get(lang, textes_societe["fr"])["type"].format(type_societe=type_societe)
            pdf.multi_cell(0, 8, txt=clean_text(texte_type), align="L")
            pdf.ln(8)
    else:
        texte_non = textes_societe.get(lang, textes_societe["fr"])["non"]
        pdf.multi_cell(0, 8, txt=clean_text(texte_non), align="L")

    pdf.ln(10)
    pdf.add_page()
    canevas_path = "static/canevas.jpg"
    if os.path.exists(canevas_path):
        pdf.image(canevas_path, x=0, y=0, w=210, h=297)

    bouteille_path = "static/bouteille.jpg"
    pdf.set_y(30)
    if os.path.exists(bouteille_path):
        y_pos = pdf.get_y()
        pdf.image(bouteille_path, x=55, y=y_pos + 1, w=8)
        text_x = 67
    else:
        text_x = 60

    # === Titre "La donation : transmettre avec sens" (multilingue) ===
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(106, 27, 27)  # Bordeaux
    pdf.set_x(text_x)

    lang = data.get("lang", "fr")

    titre_donation = {
        "fr": "La donation : transmettre avec sens",
        "en": "Donation: Giving with Purpose",
        "nl": "De schenking: met betekenis overdragen"
    }

    pdf.cell(0, 10, titre_donation.get(lang, titre_donation["fr"]), ln=True, align="L")
    pdf.ln(6)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", size=12)

    lang = data.get("lang", "fr")
    donations = data.get("donations", "non")

    # === Textes multilingues ===
    textes_donations = {
        "fr": {
            "intro": (
                "Désirez-vous faire un cadeau à Noël, à votre compagne, à votre enfant ou à un proche ? "
                "C’est une excellente idée ! Non seulement ce geste fait plaisir, mais il peut aussi avoir un intérêt fiscal insoupçonné.\n\n"
                "Comme nous l’avons évoqué plus haut, la succession légale non préparée peut se transformer en véritable gouffre fiscal. "
                "En Belgique, selon le lien de parenté, les droits de succession peuvent grimper jusqu’à **70 % ou plus** dans certains cas. "
                "Une manière d’anticiper et d’alléger cette charge consiste à donner de son vivant : la **donation**."
            ),

            "types": (
                "Il existe deux grands types de donation :\n\n"
                "• **La donation sous seing privé**, non enregistrée, gratuite (0 %), mais soumise à une période dite de « survie » "
                "de 3 à 5 ans selon la région. En cas de décès du donateur pendant ce délai, les droits de succession restent dus.\n\n"
                "• **La donation enregistrée**, via un notaire, soumise à un droit d’enregistrement modéré (environ 3 %), "
                "mais définitivement exonérée de droits de succession. Elle offre donc sécurité et transparence.\n\n"
                "Le choix dépend du niveau de confort souhaité et de la nature du bien transmis."
            ),

            "pacte": (
                "Rédigez un **pacte adjoint** afin de formaliser la donation. "
                "Ce document, simple mais essentiel, précise la nature du don et peut contenir certaines conditions : "
                "• le **retour conventionnel** (si le donataire décède avant le donateur, le bien revient au patrimoine initial), "
                "• une **compensation financière** justifiée par une charge, "
                "• ou une **interdiction temporaire de vente** des bouteilles pendant une période déterminée. "
                "Songez également à quelques précautions particulières lors de la rédaction : "
                "mentionnez pour chaque bouteille son **millésime**, son **domaine**, et, si nécessaire, un **montant expertisé** de la bouteille."
            ),

            "transition_oui": (
                "Nous avons noté que vous avez déjà envisagé des donations par le passé. "
                "Rassurez-vous : il n’en va pas autrement pour le vin. "
                "Les mêmes principes s’appliquent, à quelques nuances près."
            ),

            "transition_non": (
                "Nous avons noté que vous n'avez pas encore envisagé de donations par le passé. "
                "Le vin constitue une manière élégante et symbolique d’envisager une première transmission."
            ),

            "vin": (
                "En effet, le vin, en tant que bien matériel et patrimonial, peut ainsi tout à fait faire l’objet d’une donation.\n\n"
                "Toutefois, certaines précautions s’imposent : faites expertiser la valeur de votre cave par un professionnel "
                "reconnu — idéalement en présence du donataire — afin d’éviter toute contestation ultérieure.\n\n"
                "Gardez malgré tout à l’esprit que la valeur de vos grands crus peut évoluer au fil du temps. Ainsi, "
                "contrairement à une somme d’argent, un cohéritier pourrait invoquer la réduction de la donation au moment "
                "du décès de votre parent, si celle-ci venait à porter atteinte à sa réserve héréditaire.\n\n"
                "Il est donc recommandé d'avoir ces questions à l'esprit lorsque vous vous faites accompagner "
                "par votre notaire ou un conseiller de confiance lors de la transmission."

            )
        },

        "en": {
            "intro": (
                "Would you like to make a gift — for Christmas, to your partner, or to your child? "
                "It’s a wonderful idea ! Not only does it bring joy, but it can also have unexpected tax advantages.\n\n"
                "As mentioned earlier, unplanned inheritance can become a financial burden. "
                "In Belgium, depending on family ties, inheritance taxes can reach **up to 70 % or more** in certain cases. "
                "A way to anticipate this is through **donation** — giving during one’s lifetime."
            ),

            "types": (
                "There are two main types of donation:\n\n"
                "• **Unregistered private donation**, free of charge (0 %), but subject to a 'survival' period of 3 to 5 years "
                "depending on the region. If the donor passes away within this period, inheritance tax remains due.\n\n"
                "• **Registered donation**, executed through a notary, subject to a modest registration tax (around 3 %), "
                "after which it becomes fully exempt from inheritance duties.\n\n"
                "The right choice depends on the desired level of security and the nature of the asset transferred."
            ),

            "pacte": (
                "Draw up an **adjunct agreement** to formalize the gift. "
                "This simple yet essential document specifies the nature of the gift and may include certain conditions: "
                "• a **conventional return clause** (if the donee passes away before the donor, the asset returns to the original estate), "
                "• a **financial compensation** justified by a charge, "
                "• or a **temporary prohibition on selling** the bottles for a set period. "
                "Also, take a few particular precautions when drafting the document: "
                "for each bottle, specify its **vintage**, **estate**, and, if necessary, an **appraised value**."
            ),

            "transition_oui": (
                "We have noted that you have already considered making donations in the past. "
                "Rest assured — it’s not so different when it comes to wine. "
                "The same legal and practical principles generally apply."
            ),

            "transition_non": (
                "We have noted that you have not yet considered making donations. "
                "Wine can be a thoughtful and meaningful way to take the first step toward transmission."
            ),

            "vin": (
                "Indeed, wine, as a tangible and patrimonial asset, can perfectly well be the subject of a donation.\n\n"
                "However, certain precautions should be taken: have the value of your wine cellar assessed by "
                "a recognized professional — ideally in the presence of the donee — to avoid any future disputes.\n\n"
                "Keep in mind that the value of fine wines may change over time. Thus, unlike a sum of money, a co-heir "
                "may invoke the reduction of the gift upon the death of your parent if it infringes on their reserved portion "
                "of the estate.\n\n"
                "It is therefore advisable to keep these considerations in mind when being assisted by your notary or a trusted "
                "advisor during the transfer."
            )
        },

        "nl": {
            "intro": (
                "Wilt u een geschenk doen — met Kerst, aan uw partner of aan uw kind ? "
                "Een uitstekend idee ! Niet alleen een mooi gebaar, maar ook fiscaal interessant.\n\n"
                "Zoals eerder vermeld, kan een niet-geplande erfenis leiden tot hoge belastingen. "
                "In België kunnen de successierechten, afhankelijk van de familieband, oplopen tot **meer dan 70 %** in bepaalde gevallen. "
                "Een manier om dit te vermijden is via **schenking** — een overdracht tijdens het leven."
            ),

            "types": (
                "Er bestaan twee hoofdvormen van schenking:\n\n"
                "• **Niet-geregistreerde schenking onderhands**, volledig gratis (0 %), "
                "maar met een 'overlevingsperiode' van 3 tot 5 jaar afhankelijk van het gewest. "
                "Bij overlijden van de schenker binnen die termijn blijven successierechten verschuldigd.\n\n"
                "• **Geregistreerde schenking**, via notaris, met een beperkt registratierecht (ongeveer 3 %), "
                "maar daarna volledig vrijgesteld van successierechten.\n\n"
                "De keuze hangt af van het gewenste comfort en de aard van het overgedragen goed."
            ),

            "pacte": (
                "Stel een **aanvullend pact** op om de schenking te formaliseren. "
                "Dit eenvoudige maar essentiële document verduidelijkt de aard van de schenking en kan bepaalde voorwaarden bevatten: "
                "• een **conventioneel terugkeerbeding** (als de begiftigde overlijdt vóór de schenker, keert het goed terug naar het oorspronkelijke vermogen), "
                "• een **financiële compensatie** gerechtvaardigd door een last, "
                "• of een **tijdelijk verkoopverbod** van de flessen gedurende een bepaalde periode. "
                "Denk ook aan enkele bijzondere voorzorgsmaatregelen bij het opstellen van het document: "
                "vermeld voor elke fles het **millésime (oogstjaar)**, het **domein**, en indien nodig een **getaxeerde waarde** van de fles."
            ),

            "transition_oui": (
                "Wij hebben genoteerd dat u in het verleden al schenkingen heeft overwogen. "
                "Wees gerust, voor wijn is het niet anders. "
                "Dezelfde principes blijven grotendeels van toepassing."
            ),

            "transition_non": (
                "Wij hebben genoteerd dat u nog geen schenkingen heeft overwogen. "
                "Wijn kan een stijlvolle en betekenisvolle manier zijn om daarmee te beginnen."
            ),

            "vin": (
                "Wijn kan immers, als een tastbaar en vermogensbestanddeel, perfect het voorwerp van een schenking zijn.\n\n"
                "Wijn, als tastbaar en vermogensbestanddeel, kan zeker het voorwerp zijn van een schenking.\n\n"
                "Toch zijn enkele voorzorgsmaatregelen aangewezen: laat de waarde van uw wijnkelder schatten door een "
                "erkende professional — bij voorkeur in aanwezigheid van de begiftigde — om latere betwistingen te vermijden.\n\n"
                "Houd er rekening mee dat de waarde van uw grote wijnen in de loop der tijd kan evolueren. In tegenstelling tot een "
                "geldsom kan een mede-erfgenaam bij het overlijden van uw ouder de vermindering van de schenking inroepen, indien "
                "deze een inbreuk vormt op zijn of haar reservatair erfdeel.\n\n"
                "Het is daarom raadzaam deze vragen in gedachten te houden wanneer u zich laat begeleiden door uw notaris of een "
                "vertrouwensadviseur bij de overdracht."
            )
        }
    }

    # === Sélection des textes ===
    texte_intro = textes_donations.get(lang, textes_donations["fr"])["intro"]
    texte_types = textes_donations.get(lang, textes_donations["fr"])["types"]
    texte_pacte = textes_donations.get(lang, textes_donations["fr"])["pacte"]
    texte_vin = textes_donations.get(lang, textes_donations["fr"])["vin"]

    if donations == "oui":
        texte_transition = textes_donations.get(lang, textes_donations["fr"])["transition_oui"]
    else:
        texte_transition = textes_donations.get(lang, textes_donations["fr"])["transition_non"]

    # === Écriture dans le PDF ===
    pdf.multi_cell(0, 8, txt=clean_text(texte_intro), align="L")
    pdf.ln(6)
    pdf.multi_cell(0, 8, txt=clean_text(texte_types), align="L")
    pdf.ln(6)
    pdf.multi_cell(0, 8, txt=clean_text(texte_pacte), align="L")
    pdf.ln(10)

    # --- NOUVELLE PAGE avant la transition ---
    pdf.add_page()
    canevas_path = "static/canevas.jpg"
    if os.path.exists(canevas_path):
        pdf.image(canevas_path, x=0, y=0, w=210, h=297)
    pdf.ln(25)

    pdf.multi_cell(0, 8, txt=clean_text(texte_transition), align="L")
    pdf.ln(6)
    pdf.multi_cell(0, 8, txt=clean_text(texte_vin), align="L")
    pdf.ln(10)

    pdf.add_page()

    # === Ajout du canevas (fond décoratif) ===
    canevas_path = "static/canevas.jpg"
    if os.path.exists(canevas_path):
        pdf.image(canevas_path, x=0, y=0, w=210, h=297)

    # === Titre "Pour conclure" (multilingue) ===
    pdf.set_font("Helvetica", style="B", size=22)
    pdf.set_text_color(128, 0, 32)  # rouge bordeaux
    pdf.ln(17)

    lang = data.get("lang", "fr")

    titre_conclusion = {
        "fr": "Pour conclure",
        "en": "In Conclusion",
        "nl": "Ter afsluiting"
    }

    pdf.cell(0, 20, titre_conclusion.get(lang, titre_conclusion["fr"]), ln=True, align="C")

    # === Ligne décorative ===
    pdf.set_draw_color(128, 0, 32)
    pdf.set_line_width(0.8)
    page_width = pdf.w
    margin = 60
    y_line = pdf.get_y()
    pdf.line(margin, y_line, page_width - margin, y_line)
    pdf.ln(15)

    # === Corps de texte ===
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", size=12)

    lang = data.get("lang", "fr")
    importance_patrimoine = data.get("importance_patrimoine", "moyenne")

    textes_conclusion = {
        "fr": {
            "faible": (
                "Vous avez indiqué accorder une importance limitée à la notion de patrimoine culturel.\n\n"
                "C’est un point de vue que nous comprenons : le vin peut avant tout être un plaisir personnel, "
                "une expérience intime, vécue dans l’instant. Mais même dans cette approche, il conserve une dimension de mémoire et d’émotion. "
                "Chaque bouteille, chaque millésime raconte une histoire — celle d’un lieu, d’un geste, d’un savoir-faire. "
                "Et c’est déjà, à sa manière, une trace patrimoniale.\n\n"
                "Puissiez-vous continuer à savourer le vin comme un art de vivre, à votre rythme et selon vos envies."
            ),

            "moyenne": (
                "Vous accordez une importance modérée à la notion de patrimoine culturel.\n\n"
                "Le vin s’inscrit justement dans cet équilibre : entre plaisir et transmission, entre culture et partage. "
                "Il n’est pas nécessaire d’être collectionneur ou héritier pour en saisir la beauté. "
                "Le vin relie, inspire et traverse le temps — il appartient à ceux qui le font vivre.\n\n"
                "Chez GrandcruX, nous croyons que chaque cave, même modeste, peut devenir le reflet d’une culture personnelle, "
                "celle du goût, du souvenir et de la transmission raisonnée."
            ),

            "elevee": (
                "Vous accordez une grande importance à la notion de patrimoine culturel.\n\n"
                "C’est là, sans doute, la plus belle manière d’aborder le vin : non comme un bien de consommation, "
                "mais comme un héritage vivant. Préserver, partager, transmettre — trois gestes qui fondent la culture du vin "
                "et qui prolongent l’histoire de ceux qui l’aiment.\n\n"
                "Chez GrandcruX, nous partageons pleinement cette vision : le vin n’est pas seulement une passion, "
                "il est un lien entre les générations, un langage universel du temps et de la terre."
            )
        },

        "en": {
            "faible": (
                "You indicated that you place limited importance on the cultural heritage aspect.\n\n"
                "That is perfectly understandable — wine can first and foremost be a personal pleasure, "
                "a moment to enjoy and to share in the present. Yet even in that, it carries memory and emotion. "
                "Each bottle tells a story — of a place, a gesture, a savoir-faire — and that, too, is a form of heritage.\n\n"
                "May you continue to enjoy wine as an art of living, in your own way and at your own pace."
            ),

            "moyenne": (
                "You give moderate importance to the idea of cultural heritage.\n\n"
                "Wine perfectly embodies that balance — between pleasure and transmission, culture and sharing. "
                "You don’t have to be a collector to appreciate its meaning. "
                "Wine connects people, inspires emotion, and stands the test of time.\n\n"
                "At GrandcruX, we believe every cellar, however humble, can become a reflection of one’s own culture — "
                "of taste, of memory, and of thoughtful transmission."
            ),

            "elevee": (
                "You attach great importance to cultural heritage.\n\n"
                "That is perhaps the most beautiful way to approach wine — not merely as a commodity, "
                "but as a living legacy. To preserve, to share, to transmit — these gestures define the culture of wine "
                "and extend the story of those who cherish it.\n\n"
                "At GrandcruX, we fully share this vision: wine is not only a passion, "
                "it is a bond between generations, a universal language of time and terroir."
            )
        },

        "nl": {
            "faible": (
                "U hecht beperkte waarde aan het culturele erfgoedaspect.\n\n"
                "Dat is volkomen begrijpelijk — wijn kan in de eerste plaats een persoonlijk genot zijn, "
                "een moment om van te genieten, hier en nu. Toch draagt hij ook een herinnering en een emotie in zich. "
                "Elke fles vertelt een verhaal — over een plaats, een gebaar, een vakmanschap — en dat is al erfgoed op zich.\n\n"
                "Moge u wijn blijven ervaren als een kunst van het leven, op uw eigen manier en in uw eigen tempo."
            ),

            "moyenne": (
                "U hecht een gemiddelde waarde aan het culturele erfgoed.\n\n"
                "Wijn belichaamt precies dat evenwicht — tussen plezier en overdracht, tussen cultuur en delen. "
                "Men hoeft geen verzamelaar te zijn om de schoonheid ervan te begrijpen. "
                "Wijn verbindt mensen, wekt emoties op en trotseert de tijd.\n\n"
                "Bij GrandcruX geloven we dat elke kelder, hoe bescheiden ook, een weerspiegeling kan worden "
                "van een persoonlijke cultuur — van smaak, herinnering en bewuste overdracht."
            ),

            "elevee": (
                "U hecht veel waarde aan cultureel erfgoed.\n\n"
                "Dat is wellicht de mooiste manier om wijn te benaderen — niet enkel als consumptiegoed, "
                "maar als levend erfgoed. Bewaren, delen, overdragen — dat zijn de gebaren die de wijncultuur vormen "
                "en het verhaal van de liefhebber voortzetten.\n\n"
                "Bij GrandcruX delen we deze visie volledig: wijn is niet alleen een passie, "
                "het is een band tussen generaties, een universele taal van tijd en terroir."
            )
        }
    }

    # === Sélection du texte selon la langue et le niveau d’importance ===
    texte_conclusion = textes_conclusion.get(lang, textes_conclusion["fr"]).get(
        importance_patrimoine, textes_conclusion["fr"]["moyenne"]
    )

    # === Écriture du texte ===
    pdf.multi_cell(0, 8, txt=clean_text(texte_conclusion), align="L")
    pdf.ln(15)

    # === Coordonnées finales ===
    pdf.set_font("Helvetica", "I", size=11)
    pdf.set_text_color(90, 0, 20)
    pdf.cell(0, 10, clean_text("info@grandcruX.com  |  www.grandcruX.com"), ln=True, align="C")
    pdf.ln(30)
    slice_path = "static/slice.jpg"
    if os.path.exists(slice_path):
        image_width = 80  # petite largeur pour un rendu discret et chic
        pdf_width = 210
        x_position = (pdf_width - image_width) / 2
        pdf.image(slice_path, x=x_position, y=None, w=image_width)
        pdf.ln(10)


    # === Mention complémentaire uniquement si une case est cochée ===
    if data.get("presentation"):
        pdf.set_font("Helvetica", "I", 11)
        pdf.set_text_color(80, 80, 80)  # gris doux
        pdf.ln(4)

        mention_texte = {
            "fr": (
                "Nous avons noté que vous étiez intéressé(e) par une présentation ou une documentation "
                "complémentaire sur le vin comme support de transmission ou sur les aspects culturels "
                "et les bonnes pratiques.\n\n"
                "N’hésitez pas à en discuter avec nos conseillers ou à consulter régulièrement les "
                "informations mises à jour sur notre site."
            ),
            "en": (
                "We have noted your interest in receiving a presentation or additional material "
                "about wine as a medium of transmission, or about its cultural aspects and best practices.\n\n"
                "Feel free to discuss this with our advisors or to check our website regularly for updates."
            ),
            "nl": (
                "We hebben genoteerd dat u geïnteresseerd bent in een presentatie of bijkomende documentatie "
                "over wijn als middel tot overdracht, of over de culturele aspecten en goede praktijken.\n\n"
                "Aarzel niet om dit te bespreken met onze adviseurs of regelmatig onze website te raadplegen "
                "voor nieuwe informatie."
            ),
        }

        # Sélectionne le texte selon la langue du formulaire
        texte = mention_texte.get(data.get("lang", "fr"), mention_texte["fr"])
        pdf.multi_cell(0, 8, txt=clean_text(texte), align="C")
        pdf.ln(10)

    remarques = data.get("remarques", "").strip()

    remarques = data.get("remarques", "").strip()
    lang = data.get("lang", "fr")

    if remarques:  # uniquement si le champ n'est pas vide
        pdf.add_page()

        # === Fond / style global ===
        pdf.set_font("Helvetica", "B", 28)
        pdf.set_text_color(128, 0, 32)  # rouge bordeaux
        pdf.ln(20)
        pdf.cell(0, 20,
                 "ANNEXE" if lang == "fr" else
                 "APPENDIX" if lang == "en" else
                 "BIJLAGE",
                 ln=True, align="C")

        # Ligne décorative sous le titre
        pdf.set_draw_color(128, 0, 32)
        pdf.set_line_width(1)
        page_width = pdf.w
        margin = 60
        y_line = pdf.get_y()
        pdf.line(margin, y_line, page_width - margin, y_line)
        pdf.ln(20)

        # === Introduction texte selon la langue ===
        pdf.set_font("Helvetica", "I", 12)
        pdf.set_text_color(0, 0, 0)

        textes_intro = {
            "fr": (
                "Nous avons noté votre commentaire et nous vous en remercions.\n\n"
                "N'hésitez pas à prendre contact avec nous afin que nous en discutions. "
                "Si une réponse écrite est souhaitée, vous pouvez apporter ce rapport lors de votre rendez-vous "
                "ou d'une conférence et nous y répondrons directement dans cet encadré."
            ),
            "en": (
                "We have noted your comment and thank you for sharing it.\n\n"
                "Please feel free to contact us if you would like to discuss it further. "
                "If a written response is required, you may bring this report to your appointment "
                "or to one of our conferences, and we will reply directly in this section."
            ),
            "nl": (
                "Wij hebben uw opmerking genoteerd en danken u daarvoor.\n\n"
                "Aarzel niet om contact met ons op te nemen als u dit verder wilt bespreken. "
                "Indien een schriftelijk antwoord gewenst is, kunt u dit rapport meenemen "
                "naar uw afspraak of een conferentie, zodat wij rechtstreeks in dit kader kunnen antwoorden."
            )
        }

        intro = textes_intro.get(lang, textes_intro["fr"])
        pdf.multi_cell(0, 8, txt=intro, align="L")
        pdf.ln(12)

        # === Encadré pointillé pour réponse ===
        y_start = pdf.get_y()
        box_height = 70
        margin_x = 20
        page_width = pdf.w
        pdf.set_draw_color(150, 150, 150)  # gris doux
        pdf.set_line_width(0.4)
        # Style pointillé
        pdf.dashed_line(margin_x, y_start, page_width - margin_x, y_start)
        pdf.dashed_line(margin_x, y_start + box_height, page_width - margin_x, y_start + box_height)
        pdf.dashed_line(margin_x, y_start, margin_x, y_start + box_height)
        pdf.dashed_line(page_width - margin_x, y_start, page_width - margin_x, y_start + box_height)

        pdf.ln(box_height + 10)

        # === Reprise du commentaire du client ===
        pdf.set_font("Helvetica", size=12)
        pdf.set_text_color(90, 0, 20)

        # Coordonnées de base
        y_start = pdf.get_y()

        # 1️⃣ Logo à gauche
        image_path = "static/question_grandcrux.jpg"
        if os.path.exists(image_path):
            pdf.image(image_path, x=10, y=y_start - 5, w=55)

        # 2️⃣ Remarque du client centrée
        pdf.set_xy(55, y_start + 8)
        pdf.multi_cell(120, 8, f"« {remarques} »", align="C")

        # 3️⃣ Espace après le bloc
        pdf.ln(40)

    pdf_filename = f"{data.get('prenom', '').replace(' ', '_')}_{data.get('nom', '').replace(' ', '_')}_conditions.pdf"
    pdf.output(pdf_filename)

    return pdf_filename

def generate_print_pdf(**data):
    pdf = FPDF()
    pdf.add_page()

    # === Logo centré ===
    image_path = "static/grandcrux.png"
    page_width = pdf.w
    img_width = 100
    img_x = (page_width - img_width) / 2
    pdf.image(image_path, x=img_x, y=10, w=img_width)
    pdf.ln(60)

    # === Langue du formulaire ===
    lang = data.get("lang", "fr")

    # === Traductions ===
    text = {
        "fr": {
            "title": "Nos formules d'impression du rapport",
            "subtitle": "(Nos options d’impression et de livraison)",
            "rows": [
                ("Remise en main propre du rapport sur rendez-vous", "GRATUIT"),
                ("Envoi du rapport par la poste", "25 EUR (+ frais de port éventuels)"),
                ("Envoi du rapport et livraison à domicile du pack découverte", "525 EUR (+ frais si hors Bruxelles)"),
                ("Formule alternative sur mesure", "Prix à discuter (sur devis)")
            ],
            "footer": "Si l'une de ces formules vous intéresse, n'hésitez pas a nous contacter.",
            "team": "L'équipe GrandcruX",
            "contact": "info@grandcruX.com"
        },
        "en": {
            "title": "Our printed report options",
            "subtitle": "(Printing and delivery packages)",
            "rows": [
                ("Printed report handover at our office", "FREE"),
                ("Printed report sent by mail", "25 EUR (+ possible shipping fees)"),
                ("Printed report and home delivery of the discovery pack", "525 EUR (+ fees outside Brussels)"),
                ("Custom-made package", "Price to be discussed (on request)")
            ],
            "footer": "If you are interested in one of these options, feel free to contact us.",
            "team": "The GrandcruX Team",
            "contact": "info@grandcruX.com"
        },
        "nl": {
            "title": "Onze formules voor het gedrukte rapport",
            "subtitle": "(Onze afdruk- en leveringsopties)",
            "rows": [
                ("Afhaling van het rapport in ons kantoor", "GRATIS"),
                ("Verzending van het rapport per post", "25 EUR (+ eventuele verzendkosten)"),
                ("Verzending van het rapport en levering van het wijnspakket", "525 EUR (+ kosten buiten Brussel)"),
                ("Alternatieve formule op maat", "Prijs te bespreken (op aanvraag)")
            ],
            "footer": "Indien u geïnteresseerd bent in een van deze formules, neem gerust contact met ons op.",
            "team": "Het GrandcruX-team",
            "contact": "info@grandcruX.com"
        }
    }

    t = text.get(lang, text["fr"])  # sécurité par défaut FR

    # === Titre principal ===
    pdf.set_text_color(128, 0, 32)  # rouge vin
    pdf.set_font("Helvetica", style='B', size=16)
    pdf.cell(0, 10, clean_text(t["title"]), ln=True, align="C")

    pdf.set_font("Helvetica", style='', size=12)
    pdf.cell(0, 8, clean_text(t["subtitle"]), ln=True, align="C")
    pdf.ln(10)

    # === Tableau des formules ===
    col1_width = 120
    col2_width = 70

    for desc, price in t["rows"]:
        pdf.set_font("Helvetica", size=12)
        pdf.cell(col1_width, 10, clean_text(desc), border=0)
        pdf.set_font("Helvetica", style='B', size=12)
        pdf.cell(col2_width, 10, clean_text(price), border=0, ln=True)

    # === Message final ===
    pdf.ln(8)
    pdf.set_font("Helvetica", style='', size=12)
    pdf.multi_cell(0, 8, clean_text(t["footer"]), align="C")
    pdf.ln(10)
    pdf.set_font("Helvetica", style='B', size=12)
    pdf.cell(0, 8, clean_text(t["team"]), ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Helvetica", style='', size=11)
    pdf.cell(0, 8, clean_text(t["contact"]), ln=True, align="C")

    # === Sauvegarde ===
    print_pdf_filename = f"{data.get('prenom', '').replace(' ', '_')}_{data.get('nom', '').replace(' ', '_')}_print_version_{lang}.pdf"
    pdf.output(print_pdf_filename)

    return print_pdf_filename


@app.route("/merci")
def merci():
    return """
    <html>
    <head>
        <meta charset="utf-8">
        <title>Merci pour votre participation à GrandcruX 🍷</title>
        <style>
            body {
                background-color: #faf7f5;
                font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                color: #400018;
                text-align: center;
                margin-top: 20%;
            }
            h2 {
                color: #800020;
                font-size: 1.9em;
                margin-bottom: 40px;
                line-height: 1.6;
            }
            a.button {
                display: inline-block;
                padding: 12px 28px;
                background-color: #800020;
                color: white;
                text-decoration: none;
                border-radius: 25px;
                font-weight: bold;
                transition: background-color 0.3s ease;
            }
            a.button:hover {
                background-color: #a83232;
            }
        </style>
    </head>
    <body>
        <h2>
            Merci pour votre participation à GrandcruX 🍷<br>
            • Thank you for your participation in GrandcruX 🍷 •<br>
            Bedankt voor uw deelname aan GrandcruX 🍷
        </h2>
        <a href="https://www.grandcrux.com/vins-investissement/" class="button">Website</a>
    </body>
    </html>
    """

@app.route('/create_person', methods=['POST'])
def create_person():
    # Reçoit des données en JSON
    data = request.json
    print("Données reçues :", data) 
    
    # Récupération des données avec des valeurs par défaut
    nom = data.get('nom', 'PROSPECT')
    prenom = data.get('prenom')
    mail = data.get('mail')
    tel = data.get('tel')
    domicile = data.get('domicile', '')

    try:
        pdf_filename = generate_pdf(nom, prenom, mail, tel, domicile)

        # Ajout de la personne dans la base de données
        db_handler.create_person(nom, prenom, "", "", "", mail, tel, domicile, "")

        send_pdf_by_email(data, pdf_filename)

        return jsonify({"message": "Personne ajoutée avec succès!", "pdf_filename": pdf_filename}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def send_pdf_by_email(data, pdf_filename, print_pdf_filename=None):
    try:
        recipient_email = data.get("mail")
        if not recipient_email:
            raise ValueError("Adresse e-mail du destinataire manquante.")

        lang = data.get("lang", "fr")  # Langue du formulaire

        # --- Liste des fichiers à joindre ---
        attachments = [pdf_filename]
        if print_pdf_filename:
            attachments.append(print_pdf_filename)

        # --- Textes HTML multilingues ---
        html_textes = {
            "fr": """\
                <p>Bonjour,</p>
                <p>Veuillez trouver en pièce jointe votre rapport personnalisé sur le vin!</p>
                <p>N'hésitez pas à nous rencontrer :</p>
                <ul>
                    <li>en vous inscrivant à nos conférences, en cliquant sur 
                        <a href="https://www.grandcrux.com/conference/" 
                        style="color: blue; text-decoration: underline;">ce lien</a>;</li>
                    <li>en fixant un rendez-vous directement avec un de nos conseillers, en nous écrivant à 
                        <a href="mailto:info@grandcrux.com?subject=Prise%20de%20rendez-vous%20avec%20un%20conseiller"
                        style="color: blue; text-decoration: underline;">info@grandcrux.com</a>.</li>
                </ul>
                <p>Vous souhaitez nous contacter pour toutes autres questions ? 
                N'hésitez pas à nous écrire à 
                <a href="mailto:info@grandcrux.com" style="color: blue; text-decoration: underline;">info@grandcrux.com</a>.</p>
                <p>Nous espérons vous revoir très bientôt!</p>
                <p>Cordialement,<br>L’équipe GrandcruX</p>
            """,

            "en": """\
                <p>Hello,</p>
                <p>Please find attached your personalised wine report!</p>
                <p>We would be delighted to meet you:</p>
                <ul>
                    <li>by registering for our conferences via 
                        <a href="https://www.grandcrux.com/conference/" 
                        style="color: blue; text-decoration: underline;">this link</a>;</li>
                    <li>by scheduling an appointment directly with one of our advisors by writing to 
                        <a href="mailto:info@grandcrux.com?subject=Appointment%20with%20a%20GrandcruX%20advisor"
                        style="color: blue; text-decoration: underline;">info@grandcrux.com</a>.</li>
                </ul>
                <p>For any other questions, feel free to contact us at 
                <a href="mailto:info@grandcrux.com" style="color: blue; text-decoration: underline;">info@grandcrux.com</a>.</p>
                <p>We hope to see you again soon!</p>
                <p>Kind regards,<br>The GrandcruX Team</p>
            """,

            "nl": """\
                <p>Hallo,</p>
                <p>In de bijlage vindt u uw gepersonaliseerd wijnrapport!</p>
                <p>We ontmoeten u graag:</p>
                <ul>
                    <li>door u in te schrijven voor onze conferenties via 
                        <a href="https://www.grandcrux.com/conference/" 
                        style="color: blue; text-decoration: underline;">deze link</a>;</li>
                    <li>door rechtstreeks een afspraak te maken met een van onze adviseurs via 
                        <a href="mailto:info@grandcrux.com?subject=Afspraak%20met%20een%20GrandcruX-adviseur"
                        style="color: blue; text-decoration: underline;">info@grandcrux.com</a>.</li>
                </ul>
                <p>Voor andere vragen kunt u ons bereiken via 
                <a href="mailto:info@grandcrux.com" style="color: blue; text-decoration: underline;">info@grandcrux.com</a>.</p>
                <p>We hopen u binnenkort weer te zien!</p>
                <p>Met vriendelijke groet,<br>Het GrandcruX-team</p>
            """
        }

        # --- Sujet du mail multilingue ---
        subject_textes = {
            "fr": "Votre rapport sur le vin!",
            "en": "Your personalised wine report!",
            "nl": "Uw gepersonaliseerd wijnrapport!"
        }

        # --- Création du message ---
        msg = Message(
            subject_textes.get(lang, subject_textes["fr"]),
            recipients=[recipient_email],
            sender=app.config["MAIL_DEFAULT_SENDER"],
            bcc=['noreply@grandcrux.com']
        )
        # --- Corps du mail dynamique selon la langue ---
        msg.html = html_textes.get(lang, html_textes["fr"])

        # --- Attache les fichiers PDF ---
        for file_path in attachments:
            with app.open_resource(file_path) as pdf:
                filename = os.path.basename(file_path)
                msg.attach(filename, "application/pdf", pdf.read())

        # --- Envoi du mail ---
        mail.send(msg)
        print("Email envoyé avec succès !")
        return "Email envoyé avec succès !"

    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email : {str(e)}")
        return f"Erreur lors de l'envoi de l'email : {str(e)}"

@app.route("/", methods=["GET", "POST"])
def grandcrux_form():
    if request.method == "POST":
        # Récupère la langue actuelle du formulaire (champ caché <input name="lang">)
        lang = request.form.get("lang", "fr")

        # Petit helper pour récupérer les champs selon la langue
        def f(name):
            return request.form.get(f"{name}_{lang}")

        def f_list(name):
            # pour les checkboxes
            return request.form.getlist(f"{name}_{lang}")

        data = {
            "lang": lang,
            "age": f("age"),
            "relation_vin": f("relation_vin"),
            "connaissance_vin": f("connaissance_vin"),
            "region_preferee": f("region_preferee"),
            "budget_vin": f("budget_vin"),
            "forme_possession": f("forme_possession"),
            "motivation": f("motivation"),
            "risque": f("risque"),
            "enfants": f("enfants"),
            "nombre_enfants": f("nombre_enfants"),
            "mariage": f("mariage"),
            "regime": f("regime"),
            "societe": f("societe"),
            "type_societe": f("type_societe"),
            "donations": f("donations"),
            "importance_patrimoine": f("importance_patrimoine"),
            "presentation": [
                *f_list("presentation_transmission"),
                *f_list("presentation_aspects_culturels")
            ],
            "remarques": f("remarques"),
            "nom": f("nom"),
            "prenom": f("prenom"),
            "mail": f("mail"),
            "tel": f("tel"),
            "domicile": f("domicile"),
            "printOption": request.form.get("printOption") == "on",
        }

        print("=== Données reçues ===")
        for k, v in data.items():
            print(f"{k}: {v}")


        pdf_filename = generate_pdf(**data)

        print_pdf_filename = None
        if data["printOption"]:
            print_pdf_filename = generate_print_pdf(**data)

        send_pdf_by_email(data, pdf_filename, print_pdf_filename)

        try:
            db_handler.create_person(
                nom=data["nom"],
                prenom=data["prenom"],
                naissance=None,
                lieu=None,
                nationalite=None,
                mail=data["mail"],
                tel=data["tel"],
                domicile=data["domicile"],
                profession=None
            )
            print("✅ Données enregistrées dans la base PostgreSQL du VPS.")
        except Exception as e:
            print("❌ Erreur lors de l'enregistrement en base :", e)

        return redirect(url_for("merci"))

    return render_template("form.html")

if __name__ == "__main__":
    app.run(debug=True)
