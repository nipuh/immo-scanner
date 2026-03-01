"""
Bierdeckelrechnung nach Immocation-Methode
==========================================

Kernformel: Bruttomietrendite = (Jahreskaltmiete / Kaufpreis) * 100

Deine Kriterien:
- Normalvermietung: mind. 5% Bruttomietrendite
- WG-Vermietung:   mind. 6% Bruttomietrendite
- Max. Kaufpreis:  110.000 EUR pro Zimmer
"""

import re
import logging

logger = logging.getLogger(__name__)


class BierdeckelEvaluator:
    def __init__(self, config: dict):
        self.config = config
        self.bd = config.get('bierdeckel', {})
        self.scoring = config.get('scoring', {})
        self.bonus_config = config.get('bonuses', {})

        # Normalvermietung
        self.miete_normal_qm = self.bd.get('miete_normal_qm', 12.0)
        self.min_rendite_normal = self.bd.get('min_rendite_normal', 5.0)

        # WG-Vermietung
        self.miete_wg_zimmer = self.bd.get('miete_wg_zimmer', 420.0)
        self.min_rendite_wg = self.bd.get('min_rendite_wg', 6.0)

        # Kaufnebenkosten
        self.nk_ohne_makler = self.bd.get('nk_ohne_makler', 0.07)
        self.nk_mit_makler = self.bd.get('nk_mit_makler', 0.1057)

        # Kriterien
        self.max_preis_pro_zimmer = config.get('max_preis_pro_zimmer', 110000)
        self.gute_stadtteile = config.get('gute_stadtteile', [])

    def evaluate(self, listing: dict) -> dict:
        """Fuehrt die komplette Bierdeckelrechnung durch."""
        result = listing.copy()

        price = listing.get('price', 0)
        rooms = listing.get('rooms', 0)
        sqm = listing.get('sqm', 0) or 0
        title_lower = listing.get('title', '').lower()
        address = listing.get('address', '').lower()
        description = listing.get('description', '').lower()

        # Ausschlusskriterien pruefen
        result['excluded'] = False
        result['exclude_reason'] = ''

        exclusions = [
            ('erbbaurecht', 'Erbbaurecht'),
            ('zwangsversteigerung', 'Zwangsversteigerung'),
            ('versteigerung', 'Zwangsversteigerung'),
            ('neubau', 'Neubau'),
            ('erstbezug', 'Neubau/Erstbezug'),
            ('haus', 'Haus statt Wohnung'),
            ('villa', 'Villa (kein Apt)'),
            ('grundstueck', 'Grundstueck'),
        ]

        for keyword, reason in exclusions:
            if keyword in title_lower or keyword in description:
                result['excluded'] = True
                result['exclude_reason'] = reason
                break

        if result['excluded']:
            result['score'] = 0
            result['rendite_normal'] = 0.0
            result['rendite_wg'] = 0.0
            result['interessant'] = False
            return result

        # Grundlegende Validierung
        if not price or price <= 0:
            result['score'] = 0
            result['rendite_normal'] = 0.0
            result['rendite_wg'] = 0.0
            result['interessant'] = False
            return result

        # Preis pro Zimmer
        preis_pro_zimmer = (price / rooms) if rooms and rooms > 0 else price
        result['preis_pro_zimmer'] = round(preis_pro_zimmer)

        # Renditeberechnungen
        rendite_normal = self._calc_rendite_normal(price, sqm)
        rendite_wg = self._calc_rendite_wg(price, rooms)

        result['rendite_normal'] = round(rendite_normal, 2)
        result['rendite_wg'] = round(rendite_wg, 2)

        # Kauffaktor
        if sqm and sqm > 0:
            jahreskaltmiete_normal = self.miete_normal_qm * sqm * 12
            result['kaufpreisfaktor'] = round(price / jahreskaltmiete_normal, 1) if jahreskaltmiete_normal > 0 else 99
        else:
            result['kaufpreisfaktor'] = 99

        # Scoring
        score = 0

        # 1. Rendite Normal (35 Punkte max)
        rendite_weight = self.scoring.get('rendite_normal', 35)
        if rendite_normal >= self.min_rendite_normal:
            score += rendite_weight
        elif rendite_normal >= self.min_rendite_normal * 0.8:
            score += int(rendite_weight * 0.6)
        elif rendite_normal >= self.min_rendite_normal * 0.6:
            score += int(rendite_weight * 0.3)

        # 2. Rendite WG (25 Punkte max)
        wg_weight = self.scoring.get('rendite_wg', 25)
        if rendite_wg >= self.min_rendite_wg:
            score += wg_weight
        elif rendite_wg >= self.min_rendite_wg * 0.8:
            score += int(wg_weight * 0.6)
        elif rendite_wg >= self.min_rendite_wg * 0.6:
            score += int(wg_weight * 0.3)

        # 3. Preis pro Zimmer (20 Punkte max)
        pz_weight = self.scoring.get('preis_pro_zimmer', 20)
        if preis_pro_zimmer <= self.max_preis_pro_zimmer:
            score += pz_weight
        elif preis_pro_zimmer <= self.max_preis_pro_zimmer * 1.1:
            score += int(pz_weight * 0.5)

        # 4. Lage (10 Punkte max)
        lage_weight = self.scoring.get('lage', 10)
        for stadtteil in self.gute_stadtteile:
            if stadtteil.lower() in address:
                score += lage_weight
                break

        # 5. Leerstand Bonus (5 Punkte)
        leerstand_bonus = self.scoring.get('leerstand', 5)
        leerstand_keywords = ['leer', 'leerstand', 'sofort frei', 'sofort beziehbar', 'unbewohnt']
        for kw in leerstand_keywords:
            if kw in title_lower or kw in description:
                score += leerstand_bonus
                result['leerstand'] = True
                break
        else:
            result['leerstand'] = False

        # 6. WG-geeignet Bonus (5 Punkte)
        wg_bonus = self.scoring.get('wg_geeignet', 5)
        wg_keywords = ['wg', 'wg-geeignet', 'wg geeignet', 'mehrzimmer', 'wohngemeinschaft']
        if rooms and rooms >= 3:
            score += wg_bonus
            result['wg_geeignet'] = True
        else:
            for kw in wg_keywords:
                if kw in title_lower or kw in description:
                    score += wg_bonus
                    result['wg_geeignet'] = True
                    break
            else:
                result['wg_geeignet'] = False

        result['score'] = min(score, 100)

        # "Interessant" wenn Score >= 30 ODER Rendite ueber Schwelle
        result['interessant'] = (
            score >= 30
            or rendite_normal >= self.min_rendite_normal
            or rendite_wg >= self.min_rendite_wg
        )

        # Empfehlung
        result['empfehlung'] = self._generate_empfehlung(result)

        return result

    def _calc_rendite_normal(self, price: float, sqm: float) -> float:
        """Berechnet Bruttomietrendite fuer Normalvermietung."""
        if not sqm or sqm <= 0 or not price or price <= 0:
            return 0.0
        jahreskaltmiete = self.miete_normal_qm * sqm * 12
        return (jahreskaltmiete / price) * 100

    def _calc_rendite_wg(self, price: float, rooms: float) -> float:
        """Berechnet Bruttomietrendite fuer WG-Vermietung."""
        if not rooms or rooms <= 0 or not price or price <= 0:
            return 0.0
        jahreskaltmiete = self.miete_wg_zimmer * rooms * 12
        return (jahreskaltmiete / price) * 100

    def _generate_empfehlung(self, result: dict) -> str:
        """Generiert eine kurze Empfehlung."""
        score = result.get('score', 0)
        rendite_n = result.get('rendite_normal', 0)
        rendite_wg = result.get('rendite_wg', 0)

        if score >= 70:
            return 'SEHR INTERESSANT - sofort pruefen!'
        elif score >= 50:
            return f'Interessant: {rendite_n:.1f}% Rendite normal, {rendite_wg:.1f}% WG'
        elif score >= 30:
            return f'Pruefen: {rendite_n:.1f}% Rendite (Ziel: {self.min_rendite_normal}%)'
        else:
            return f'Unter Schwelle: {rendite_n:.1f}% Rendite normal'
