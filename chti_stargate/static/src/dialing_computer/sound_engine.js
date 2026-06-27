/** @odoo-module **/

/**
 * Moteur audio synthétique du Dialing Computer (Web Audio API).
 *
 * Aucun fichier sonore : tout est généré à la volée (oscillateurs + bruit filtré).
 * Univers parallèle — bruitages originaux, sans rapport avec les sons du show.
 */
export class StargateAudio {
    constructor() {
        this.ctx = null;
        this.master = null;
        this.muted = false;
        this._spin = null;
        this._ambient = null;
    }

    /** Crée (paresseusement) le contexte audio. Doit être appelé depuis un geste utilisateur. */
    _ensure() {
        if (!this.ctx) {
            const AC = window.AudioContext || window.webkitAudioContext;
            if (!AC) {
                return false;
            }
            this.ctx = new AC();
            this.master = this.ctx.createGain();
            this.master.gain.value = this.muted ? 0 : 0.8;
            this.master.connect(this.ctx.destination);
        }
        if (this.ctx.state === "suspended") {
            this.ctx.resume();
        }
        return true;
    }

    setMuted(muted) {
        this.muted = muted;
        if (this.master) {
            this.master.gain.value = muted ? 0 : 0.8;
        }
    }

    _noiseBuffer(duration) {
        const len = Math.floor(this.ctx.sampleRate * duration);
        const buf = this.ctx.createBuffer(1, len, this.ctx.sampleRate);
        const data = buf.getChannelData(0);
        for (let i = 0; i < len; i++) {
            data[i] = Math.random() * 2 - 1;
        }
        return buf;
    }

    /** Vrombissement grave de l'anneau pendant la rotation. */
    startSpin() {
        if (!this._ensure() || this._spin) {
            return;
        }
        const ctx = this.ctx;
        const t = ctx.currentTime;
        const osc = ctx.createOscillator();
        osc.type = "sawtooth";
        osc.frequency.value = 54;
        const lfo = ctx.createOscillator(); // léger trémolo mécanique
        lfo.frequency.value = 11;
        const lfoGain = ctx.createGain();
        lfoGain.gain.value = 7;
        lfo.connect(lfoGain).connect(osc.frequency);
        const filter = ctx.createBiquadFilter();
        filter.type = "lowpass";
        filter.frequency.value = 300;
        const gain = ctx.createGain();
        gain.gain.setValueAtTime(0.0001, t);
        gain.gain.linearRampToValueAtTime(0.16, t + 0.3);
        osc.connect(filter).connect(gain).connect(this.master);
        osc.start();
        lfo.start();
        this._spin = { osc, lfo, gain };
    }

    stopSpin() {
        if (!this._spin) {
            return;
        }
        const { osc, lfo, gain } = this._spin;
        const t = this.ctx.currentTime;
        gain.gain.cancelScheduledValues(t);
        gain.gain.setValueAtTime(gain.gain.value, t);
        gain.gain.linearRampToValueAtTime(0.0001, t + 0.2);
        osc.stop(t + 0.25);
        lfo.stop(t + 0.25);
        this._spin = null;
    }

    /** Verrouillage du chevron : impact grave et vibrant (clunk lourd avec traîne résonnante). */
    lock() {
        if (!this._ensure()) {
            return;
        }
        const ctx = this.ctx;
        const t = ctx.currentTime;

        // Corps de l'impact : descend très bas, sans glissando "cartoon".
        const body = ctx.createOscillator();
        body.type = "triangle";
        body.frequency.setValueAtTime(92, t);
        body.frequency.exponentialRampToValueAtTime(34, t + 0.3);

        // Traîne vibrante : deux sinus graves désaccordés -> battement ~5 Hz.
        const res1 = ctx.createOscillator();
        res1.type = "sine";
        res1.frequency.value = 57;
        const res2 = ctx.createOscillator();
        res2.type = "sine";
        res2.frequency.value = 62;

        // Passe-bas résonnant : donne le "ring" métallique grave.
        const lp = ctx.createBiquadFilter();
        lp.type = "lowpass";
        lp.frequency.setValueAtTime(850, t);
        lp.frequency.exponentialRampToValueAtTime(150, t + 0.3);
        lp.Q.value = 7;

        const g = ctx.createGain();
        g.gain.setValueAtTime(0.0001, t);
        g.gain.linearRampToValueAtTime(0.8, t + 0.008); // attaque sèche
        g.gain.exponentialRampToValueAtTime(0.22, t + 0.16);
        g.gain.exponentialRampToValueAtTime(0.0001, t + 0.65); // longue traîne vibrante

        body.connect(lp);
        res1.connect(lp);
        res2.connect(lp);
        lp.connect(g).connect(this.master);
        body.start(t);
        res1.start(t);
        res2.start(t);
        body.stop(t + 0.66);
        res1.stop(t + 0.66);
        res2.stop(t + 0.66);

        // Transitoire d'impact : claquement mat et grave (bruit passe-bas, très court).
        const noise = ctx.createBufferSource();
        noise.buffer = this._noiseBuffer(0.06);
        const nf = ctx.createBiquadFilter();
        nf.type = "lowpass";
        nf.frequency.value = 550;
        const ng = ctx.createGain();
        ng.gain.setValueAtTime(0.45, t);
        ng.gain.exponentialRampToValueAtTime(0.001, t + 0.06);
        noise.connect(nf).connect(ng).connect(this.master);
        noise.start(t);
        noise.stop(t + 0.07);
    }

    /** Whoosh du kawoosh à l'établissement du vortex. */
    kawoosh() {
        if (!this._ensure()) {
            return;
        }
        const ctx = this.ctx;
        const t = ctx.currentTime;
        const noise = ctx.createBufferSource();
        noise.buffer = this._noiseBuffer(1.7);
        const filter = ctx.createBiquadFilter();
        filter.type = "bandpass";
        filter.Q.value = 0.8;
        filter.frequency.setValueAtTime(160, t);
        filter.frequency.exponentialRampToValueAtTime(2400, t + 0.35);
        filter.frequency.exponentialRampToValueAtTime(110, t + 1.5);
        const g = ctx.createGain();
        g.gain.setValueAtTime(0.001, t);
        g.gain.exponentialRampToValueAtTime(0.6, t + 0.3);
        g.gain.exponentialRampToValueAtTime(0.001, t + 1.6);
        noise.connect(filter).connect(g).connect(this.master);
        noise.start(t);
        noise.stop(t + 1.7);
    }

    /** Grondement d'ambiance pendant que le vortex est ouvert. */
    startAmbient() {
        if (!this._ensure() || this._ambient) {
            return;
        }
        const ctx = this.ctx;
        const t = ctx.currentTime;
        const osc = ctx.createOscillator();
        osc.type = "sine";
        osc.frequency.value = 46;
        const osc2 = ctx.createOscillator();
        osc2.type = "sine";
        osc2.frequency.value = 69; // léger battement avec le fondamental
        const g = ctx.createGain();
        g.gain.setValueAtTime(0.0001, t);
        g.gain.linearRampToValueAtTime(0.12, t + 1.0);
        osc.connect(g);
        osc2.connect(g);
        g.connect(this.master);
        osc.start();
        osc2.start();
        this._ambient = { osc, osc2, g };
    }

    stopAmbient() {
        if (!this._ambient) {
            return;
        }
        const { osc, osc2, g } = this._ambient;
        const t = this.ctx.currentTime;
        g.gain.cancelScheduledValues(t);
        g.gain.setValueAtTime(g.gain.value, t);
        g.gain.linearRampToValueAtTime(0.0001, t + 0.6);
        osc.stop(t + 0.7);
        osc2.stop(t + 0.7);
        this._ambient = null;
    }

    dispose() {
        this.stopSpin();
        this.stopAmbient();
        if (this.ctx) {
            this.ctx.close();
            this.ctx = null;
        }
    }
}
