/** @odoo-module **/

import { registry } from "@web/core/registry";
import { DialingComputer } from "./dialing_computer";

/**
 * Variante publique (front website, sans login) du Dialing Computer.
 * Les données sont lues via le contrôleur /stargate/data (sudo côté serveur) ;
 * aucune journalisation et pas de bouton de retour vers le backend.
 */
export class DialingComputerPublic extends DialingComputer {
    get isPublic() {
        return true;
    }

    async _loadData() {
        const res = await fetch("/stargate/data");
        const data = await res.json();
        return [data.glyphs || [], data.planets || []];
    }

    exit() {
        // Pas de retour vers le backend en accès public.
    }
}

registry.category("public_components").add("chti_stargate.DialingComputerPublic", DialingComputerPublic);
