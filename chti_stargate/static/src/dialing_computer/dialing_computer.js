/** @odoo-module **/

import { Component, useState, useRef, onWillStart, onWillUnmount, markup } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { browser } from "@web/core/browser/browser";
import { StargateAudio } from "./sound_engine";

// Gate geometry (SVG user units).
const GATE_SIZE = 540;
const CENTER = GATE_SIZE / 2;
const CHEVRON_COUNT = 9;
const CHEVRON_RADIUS = 226; // distance from center to each chevron
const TICK_COUNT = 39; // one tick per Milky Way glyph
const RING_GLYPH_RADIUS = 200; // radius at which the 39 glyphs sit on the spinning ring
const RING_STEP = 360 / TICK_COUNT; // angular gap between two glyphs on the ring

// Clockwise order in which the chevrons glow as each symbol is encoded.
// The top chevron (index 0) is the physical lock and lights last (7th symbol).
const CHEVRON_LIGHT_ORDER = [1, 8, 2, 7, 3, 6, 0];

const COORDINATE_FIELDS = [
    "glyph_1_id", "glyph_2_id", "glyph_3_id",
    "glyph_4_id", "glyph_5_id", "glyph_6_id", "glyph_7_id",
];

/**
 * Ordinateur de numérotation (Dialing Computer) — reproduction de l'interface SG-1.
 * Anneau + 9 chevrons, grille des 39 glyphes, slots de l'adresse, composition animée.
 */
export class DialingComputer extends Component {
    static template = "chti_stargate.DialingComputer";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.rootRef = useRef("root");
        this.audio = new StargateAudio();
        onWillUnmount(() => this.audio.dispose());

        this.state = useState({
            glyphs: [],            // les 39 glyphes
            planets: [],           // destinations connues
            sequence: [],          // glyphes verrouillés (objets glyphe)
            litChevrons: [],       // index des chevrons illuminés (rouge)
            revealedCount: 0,      // nb de slots remplis (révélés)
            ringAngle: 0,          // rotation courante de l'anneau des symboles (deg, cumulé)
            ringDuration: 0,       // durée de la rotation en cours (s) — vitesse angulaire constante
            topLocking: false,     // le chevron du haut plonge pour verrouiller
            status: "IDLE",        // IDLE | DIALING | ENGAGED
            selectedPlanetId: false,
            dialing: false,
            kawoosh: false,        // éruption instable du vortex (transitoire)
            muted: false,          // coupe le son
        });

        onWillStart(async () => {
            const [glyphs, planets] = await this._loadData();
            // Pré-rend la forme SVG de chaque glyphe (currentColor → couleur du thème).
            for (const g of glyphs) {
                g.shape = g.svg ? markup(g.svg) : false;
            }
            this.state.glyphs = glyphs;
            this.state.planets = planets;
        });
    }

    /** Vrai côté front public (lecture via contrôleur, pas de journalisation). */
    get isPublic() {
        return false;
    }

    /** Charge glyphes + destinations (backend : via ORM). */
    async _loadData() {
        return Promise.all([
            this.orm.searchRead(
                "stargate.glyph",
                [["gate_type", "=", "milky_way"]],
                ["number", "name", "is_point_of_origin", "svg"],
                { order: "number" }
            ),
            this.orm.searchRead(
                "stargate.planet",
                [],
                ["name", "designation", "address_display", ...COORDINATE_FIELDS, "point_of_origin_id"],
                { order: "name" }
            ),
        ]);
    }

    // --- Géométrie de l'anneau ---------------------------------------------

    get gateSize() {
        return GATE_SIZE;
    }

    get center() {
        return CENTER;
    }

    /** Position et orientation des 9 chevrons autour de l'anneau. */
    get chevrons() {
        const list = [];
        for (let i = 0; i < CHEVRON_COUNT; i++) {
            // Chevron 0 en haut, puis sens horaire.
            const angle = -90 + (360 / CHEVRON_COUNT) * i;
            const rad = (angle * Math.PI) / 180;
            list.push({
                index: i,
                x: CENTER + CHEVRON_RADIUS * Math.cos(rad),
                y: CENTER + CHEVRON_RADIUS * Math.sin(rad),
                rotation: angle + 90, // le caret pointe vers le centre
                locked: this.state.litChevrons.includes(i),
                isTop: i === 0,
            });
        }
        return list;
    }

    /** Graduations (39 glyphes) sur l'anneau intérieur (tourne avec lui). */
    get ticks() {
        const list = [];
        for (let i = 0; i < TICK_COUNT; i++) {
            const angle = -90 + RING_STEP * i;
            list.push({ index: i, rotation: angle });
        }
        return list;
    }

    /** Les 39 glyphes gravés sur l'anneau intérieur (positionnés en cercle, tournent avec). */
    get ringGlyphs() {
        return this.state.glyphs.map((g, i) => {
            const angle = -90 + RING_STEP * i;
            const rad = (angle * Math.PI) / 180;
            return {
                id: g.id,
                shape: g.shape,
                number: g.number,
                x: CENTER + RING_GLYPH_RADIUS * Math.cos(rad),
                y: CENTER + RING_GLYPH_RADIUS * Math.sin(rad),
                rotation: angle + 90, // gravé radialement, pointe vers le centre
            };
        });
    }

    /** Les 7 emplacements de l'adresse (6 coordonnées + point d'origine). */
    get slots() {
        const slots = [];
        for (let i = 0; i < 7; i++) {
            slots.push({
                position: i + 1,
                glyph: (i < this.state.revealedCount && this.state.sequence[i]) || false,
            });
        }
        return slots;
    }

    get addressText() {
        if (!this.state.sequence.length) {
            return "";
        }
        return this.state.sequence.map((g) => g.number).join("-");
    }

    // --- Interactions -------------------------------------------------------

    /** Quitte l'interface immersive et revient au menu racine d'Odoo (grille des apps). */
    exit() {
        if (this.state.dialing) {
            return;
        }
        this.audio.dispose();
        browser.location.href = "/odoo";
    }

    toggleMute() {
        this.state.muted = !this.state.muted;
        this.audio.setMuted(this.state.muted);
    }

    addGlyph(glyph) {
        if (this.state.dialing || this.state.status === "ENGAGED") {
            return;
        }
        if (this.state.sequence.length >= 7) {
            this.notification.add("Address sequence is full (7 symbols).", { type: "warning" });
            return;
        }
        if (this.state.sequence.some((g) => g.id === glyph.id)) {
            return; // un glyphe ne s'utilise qu'une fois
        }
        this.state.sequence.push(glyph);
        this.state.revealedCount = this.state.sequence.length;
        this.state.status = "DIALING";
    }

    removeLast() {
        if (this.state.dialing) {
            return;
        }
        this.state.sequence.pop();
        this.state.revealedCount = this.state.sequence.length;
        this.state.status = this.state.sequence.length ? "DIALING" : "IDLE";
    }

    reset() {
        if (this.state.dialing) {
            return;
        }
        this.state.sequence = [];
        this.state.litChevrons = [];
        this.state.revealedCount = 0;
        this.state.ringAngle = 0;
        this.state.topLocking = false;
        this.state.status = "IDLE";
        this.state.selectedPlanetId = false;
        this.audio.stopAmbient();
    }

    /** Pré-remplit la séquence depuis une destination connue. */
    loadPlanet(ev) {
        const planetId = parseInt(ev.target.value, 10);
        this.state.selectedPlanetId = planetId || false;
        this.state.sequence = [];
        this.state.litChevrons = [];
        this.state.revealedCount = 0;
        this.state.ringAngle = 0;
        this.state.topLocking = false;
        this.state.status = "IDLE";
        this.audio.stopAmbient();
        if (!planetId) {
            return;
        }
        const planet = this.state.planets.find((p) => p.id === planetId);
        if (!planet) {
            return;
        }
        const glyphById = Object.fromEntries(this.state.glyphs.map((g) => [g.id, g]));
        const seq = [];
        for (const field of COORDINATE_FIELDS) {
            const ref = planet[field];
            if (ref && glyphById[ref[0]]) {
                seq.push(glyphById[ref[0]]);
            }
        }
        const poo = planet.point_of_origin_id;
        if (poo && glyphById[poo[0]]) {
            seq.push(glyphById[poo[0]]);
        }
        this.state.sequence = seq;
        this.state.revealedCount = seq.length;
        this.state.status = "DIALING";
    }

    /**
     * Composition animée (numérotation manuelle, façon Porte terrienne) :
     * pour chaque symbole l'anneau des glyphes tourne — en alternant le sens —
     * jusqu'à amener le glyphe sous le chevron du haut, qui plonge pour le
     * verrouiller, puis le chevron correspondant s'illumine en rouge.
     */
    async dial() {
        if (this.state.dialing || !this.state.sequence.length) {
            return;
        }
        this.state.dialing = true;
        this.state.status = "DIALING";
        this.state.litChevrons = [];
        this.state.revealedCount = 0;
        this.state.topLocking = false;
        const seq = this.state.sequence;
        await this._sleep(400);

        for (let i = 0; i < seq.length; i++) {
            // 1. l'anneau tourne (sens alterné) pour aligner le glyphe en haut
            await this._spinTo(seq[i], i);
            await this._sleep(200);
            // 2. le chevron du haut plonge et verrouille le symbole
            await this._lockTopChevron();
            // 3. la case se remplit et le chevron de la séquence s'illumine
            this.state.revealedCount = i + 1;
            this.state.litChevrons = [
                ...this.state.litChevrons,
                CHEVRON_LIGHT_ORDER[i % CHEVRON_LIGHT_ORDER.length],
            ];
            await this._sleep(350);
        }

        await this._sleep(500);
        // KAWOOSH — le vortex instable jaillit puis se stabilise en flaque (event horizon).
        this.state.status = "ENGAGED";
        this.state.kawoosh = true;
        this.audio.kawoosh();
        await this._sleep(1500);
        this.state.kawoosh = false;
        this.state.dialing = false;
        this.audio.startAmbient();

        // Journalise la connexion si on a sélectionné une destination connue (backend seulement).
        if (this.state.selectedPlanetId && !this.isPublic) {
            await this.orm.call("stargate.planet", "action_dial", [[this.state.selectedPlanetId]]);
        }
    }

    /**
     * Fait tourner l'anneau pour amener `glyph` sous le chevron du haut.
     * Le sens alterne (horaire pour les rangs pairs, antihoraire pour les impairs)
     * et chaque rotation comporte au moins un tour complet, comme la vraie porte.
     */
    async _spinTo(glyph, stepIndex) {
        const idx = this.state.glyphs.findIndex((g) => g.id === glyph.id);
        if (idx < 0) {
            await this._sleep(800);
            return;
        }
        // Rotation (mod 360) qui place le glyphe d'indice idx tout en haut.
        const targetMod = ((-RING_STEP * idx) % 360 + 360) % 360;
        const currentMod = ((this.state.ringAngle % 360) + 360) % 360;
        const dir = stepIndex % 2 === 0 ? 1 : -1; // pair = horaire, impair = antihoraire
        let delta;
        if (dir > 0) {
            delta = ((targetMod - currentMod) % 360 + 360) % 360;
        } else {
            delta = -(((currentMod - targetMod) % 360 + 360) % 360);
        }
        delta += dir * 360; // au moins un tour complet pour l'effet
        // Vitesse angulaire constante : durée proportionnelle à l'angle parcouru.
        const SPEED_DPS = 200; // degrés par seconde
        const duration = Math.abs(delta) / SPEED_DPS;
        this.state.ringDuration = duration;
        this.audio.startSpin();
        this.state.ringAngle += delta;
        await this._sleep(duration * 1000 + 60); // doit suivre la transition CSS (linéaire)
        this.audio.stopSpin();
    }

    /** Le chevron du haut plonge puis remonte pour verrouiller le symbole aligné. */
    async _lockTopChevron() {
        this.state.topLocking = true;
        this.audio.lock();
        await this._sleep(450);
        this.state.topLocking = false;
        await this._sleep(120);
    }

    _sleep(ms) {
        return new Promise((resolve) => window.setTimeout(resolve, ms));
    }
}

registry.category("actions").add("chti_stargate.dialing_computer", DialingComputer);
