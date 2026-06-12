/** @odoo-module **/

import { Component, useState, useRef, onWillStart, markup } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { browser } from "@web/core/browser/browser";

// Gate geometry (SVG user units).
const GATE_SIZE = 540;
const CENTER = GATE_SIZE / 2;
const CHEVRON_COUNT = 9;
const CHEVRON_RADIUS = 226; // distance from center to each chevron
const TICK_COUNT = 39; // one tick per Milky Way glyph

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
        this.centerRef = useRef("center");

        this.state = useState({
            glyphs: [],            // les 39 glyphes
            planets: [],           // destinations connues
            sequence: [],          // glyphes verrouillés (objets glyphe)
            lockedChevrons: 0,     // nb de chevrons enclenchés
            revealedCount: 0,      // nb de slots remplis (révélés)
            centerGlyph: false,    // glyphe affiché en grand au centre
            status: "IDLE",        // IDLE | DIALING | ENGAGED
            selectedPlanetId: false,
            dialing: false,
        });

        onWillStart(async () => {
            const [glyphs, planets] = await Promise.all([
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
            // Pré-rend la forme SVG de chaque glyphe (currentColor → couleur du thème).
            for (const g of glyphs) {
                g.shape = g.svg ? markup(g.svg) : false;
            }
            this.state.glyphs = glyphs;
            this.state.planets = planets;
        });
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
                locked: i < this.state.lockedChevrons,
            });
        }
        return list;
    }

    /** Graduations (39 glyphes) sur l'anneau intérieur. */
    get ticks() {
        const list = [];
        for (let i = 0; i < TICK_COUNT; i++) {
            const angle = -90 + (360 / TICK_COUNT) * i;
            list.push({ index: i, rotation: angle });
        }
        return list;
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
        browser.location.href = "/odoo";
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
        this.state.lockedChevrons = this.state.sequence.length;
        this.state.revealedCount = this.state.sequence.length;
        this.state.status = "DIALING";
    }

    removeLast() {
        if (this.state.dialing) {
            return;
        }
        this.state.sequence.pop();
        this.state.lockedChevrons = this.state.sequence.length;
        this.state.revealedCount = this.state.sequence.length;
        this.state.status = this.state.sequence.length ? "DIALING" : "IDLE";
    }

    reset() {
        if (this.state.dialing) {
            return;
        }
        this.state.sequence = [];
        this.state.lockedChevrons = 0;
        this.state.revealedCount = 0;
        this.state.centerGlyph = false;
        this.state.status = "IDLE";
        this.state.selectedPlanetId = false;
    }

    /** Pré-remplit la séquence depuis une destination connue. */
    loadPlanet(ev) {
        const planetId = parseInt(ev.target.value, 10);
        this.state.selectedPlanetId = planetId || false;
        this.state.sequence = [];
        this.state.lockedChevrons = 0;
        this.state.revealedCount = 0;
        this.state.centerGlyph = false;
        this.state.status = "IDLE";
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
        this.state.lockedChevrons = seq.length;
        this.state.revealedCount = seq.length;
        this.state.status = "DIALING";
    }

    /**
     * Composition animée. Pour chaque symbole : le chevron s'enclenche, le glyphe
     * s'affiche en grand au centre, puis se réduit en glissant dans sa case.
     */
    async dial() {
        if (this.state.dialing || !this.state.sequence.length) {
            return;
        }
        this.state.dialing = true;
        this.state.status = "DIALING";
        this.state.lockedChevrons = 0;
        this.state.revealedCount = 0;
        this.state.centerGlyph = false;
        const total = this.state.sequence.length;
        await this._sleep(400);

        for (let i = 1; i <= total; i++) {
            // 1. enclenchement du chevron
            this.state.lockedChevrons = i;
            await this._sleep(450);
            // 2. le glyphe apparaît en grand au centre
            this.state.centerGlyph = this.state.sequence[i - 1];
            await this._sleep(750);
            // 3. il glisse en se réduisant vers sa case
            await this._flyToSlot(i);
            // 4. la case se remplit
            this.state.revealedCount = i;
            this.state.centerGlyph = false;
            await this._sleep(250);
        }

        await this._sleep(500);
        this.state.status = "ENGAGED";
        this.state.dialing = false;

        // Journalise la connexion si on a sélectionné une destination connue.
        if (this.state.selectedPlanetId) {
            await this.orm.call("stargate.planet", "action_dial", [[this.state.selectedPlanetId]]);
        }
    }

    /** Anime le glyphe central vers la case n° i (translation + réduction). */
    async _flyToSlot(i) {
        const root = this.rootRef.el;
        const shape = this.centerRef.el;
        const target = root && root.querySelector(`.o_sg_slot[data-pos="${i}"]`);
        if (!shape || !target) {
            await this._sleep(400);
            return;
        }
        const c = shape.getBoundingClientRect();
        const t = target.getBoundingClientRect();
        const dx = t.left + t.width / 2 - (c.left + c.width / 2);
        const dy = t.top + t.height / 2 - (c.top + c.height / 2);
        const scale = Math.max(0.18, Math.min(0.45, t.height / c.height));
        shape.style.transition = "transform 0.55s ease-in, opacity 0.55s ease-in";
        shape.style.transform = `translate(${dx}px, ${dy}px) scale(${scale})`;
        shape.style.opacity = "0.15";
        await this._sleep(560);
    }

    _sleep(ms) {
        return new Promise((resolve) => window.setTimeout(resolve, ms));
    }
}

registry.category("actions").add("chti_stargate.dialing_computer", DialingComputer);
