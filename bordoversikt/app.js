/* Bordoversikt – én fil, ingen avhengigheter. All data i localStorage. */
(function () {
  'use strict';

  var LAGRINGSNOKKEL = 'bordoversikt.v1';
  var LANGT_TRYKK_MS = 550;
  var FLYTT_TOLERANSE = 12; // px før et trykk regnes som dra
  var STORRELSER = { S: 0.12, M: 0.155, L: 0.2 }; // andel av gulvets høyde

  // ---------- Data ----------
  function standardData() {
    var bord = [];
    var plasser = [
      [12, 22], [30, 22], [48, 22], [66, 22],
      [12, 55], [30, 55], [48, 55], [66, 55],
      [12, 85], [30, 85], [48, 85], [66, 85],
      [88, 30], [88, 70]
    ];
    plasser.forEach(function (p, i) {
      bord.push({
        id: nyId(), navn: String(i + 1),
        form: i >= 12 ? 'rund' : (i % 2 ? 'rund' : 'firkant'),
        storrelse: i >= 12 ? 'L' : 'M',
        x: p[0], y: p[1],
        opptatt: false, sistBesok: null, angre: null
      });
    });
    return { bord: bord, innstillinger: { gul: 10, rod: 20, pin: '1234' } };
  }

  function nyId() { return 'b' + Date.now().toString(36) + Math.random().toString(36).slice(2, 7); }

  function last() {
    try {
      var tekst = localStorage.getItem(LAGRINGSNOKKEL);
      if (tekst) {
        var d = JSON.parse(tekst);
        if (d && Array.isArray(d.bord) && d.innstillinger) return d;
      }
    } catch (e) { /* tom eller blokkert lagring */ }
    return standardData();
  }

  function lagre() {
    try { localStorage.setItem(LAGRINGSNOKKEL, JSON.stringify(data)); } catch (e) { /* ignorer */ }
  }

  var data = last();
  var redigerer = false;
  var valgtId = null;

  function finnBord(id) {
    for (var i = 0; i < data.bord.length; i++) if (data.bord[i].id === id) return data.bord[i];
    return null;
  }

  // ---------- Tid ----------
  function minutterSiden(b) {
    if (!b.opptatt || !b.sistBesok) return null;
    return Math.max(0, Math.floor((Date.now() - b.sistBesok) / 60000));
  }

  function fargeFor(min) {
    var s = data.innstillinger;
    if (min === null) return 'ledig';
    if (min < s.gul) return 'gronn';
    if (min <= s.rod) return 'gul';
    return 'rod';
  }

  function visMinutter(min) {
    if (min < 100) return min + '<small> min</small>';
    var t = Math.floor(min / 60), m = min % 60;
    return t + '<small>t</small> ' + m + '<small>m</small>';
  }

  function klokkeslett(ts) {
    var d = new Date(ts);
    return pad(d.getHours()) + ':' + pad(d.getMinutes());
  }
  function pad(n) { return (n < 10 ? '0' : '') + n; }

  // ---------- Handlinger ----------
  function taVare(b) { b.angre = { opptatt: b.opptatt, sistBesok: b.sistBesok }; }

  function besokt(b) {
    taVare(b);
    b.opptatt = true;
    b.sistBesok = Date.now();
    lagre();
    tegn();
    blink(b.id);
    visMelding('Bord ' + b.navn + ' besøkt', b.id);
  }

  function settOpptatt(b, opptatt) {
    taVare(b);
    b.opptatt = opptatt;
    b.sistBesok = opptatt ? Date.now() : null;
    lagre();
    tegn();
  }

  function angre(b) {
    if (!b.angre) return;
    b.opptatt = b.angre.opptatt;
    b.sistBesok = b.angre.sistBesok;
    b.angre = null;
    lagre();
    tegn();
  }

  // ---------- Tegning ----------
  var gulv = document.getElementById('gulv');
  var elementer = {}; // id -> element

  function bordStorrelsePx(b) {
    var h = gulv.clientHeight || 600;
    var w = gulv.clientWidth || 800;
    return Math.round(Math.min(h, w * 0.75) * (STORRELSER[b.storrelse] || STORRELSER.M));
  }

  function tegn() {
    var finnes = {};
    data.bord.forEach(function (b) {
      finnes[b.id] = true;
      var el = elementer[b.id];
      if (!el) {
        el = document.createElement('div');
        el.className = 'bord';
        el.dataset.id = b.id;
        el.setAttribute('role', 'button');
        el.innerHTML = '<span class="navn"></span><span class="tid"></span>';
        gulv.appendChild(el);
        elementer[b.id] = el;
      }
      var min = minutterSiden(b);
      var farge = redigerer ? '' : fargeFor(min);
      var klasser = 'bord ' + (b.form === 'rund' ? 'rund ' : '') + farge;
      if (redigerer && b.id === valgtId) klasser += ' valgt';
      if (el.classList.contains('drar')) klasser += ' drar';
      if (el.classList.contains('trykket')) klasser += ' trykket';
      if (el.classList.contains('blink')) klasser += ' blink';
      if (el.className !== klasser) el.className = klasser;

      el.style.setProperty('--s', bordStorrelsePx(b) + 'px');
      el.style.left = b.x + '%';
      el.style.top = b.y + '%';

      el.firstChild.textContent = b.navn;
      var tidHtml = redigerer ? '' : (min === null ? 'ledig' : visMinutter(min));
      if (el.lastChild.innerHTML !== tidHtml) el.lastChild.innerHTML = tidHtml;
      el.setAttribute('aria-label', 'Bord ' + b.navn + ', ' + (min === null ? 'ledig' : min + ' minutter siden besøk'));
    });
    Object.keys(elementer).forEach(function (id) {
      if (!finnes[id]) { elementer[id].remove(); delete elementer[id]; }
    });

    var tomt = gulv.querySelector('.tomt');
    if (!data.bord.length && !tomt) {
      tomt = document.createElement('div');
      tomt.className = 'tomt';
      tomt.textContent = 'Ingen bord ennå. Trykk «Rediger» og legg til bord.';
      gulv.appendChild(tomt);
    } else if (data.bord.length && tomt) tomt.remove();

    tegnTopp();
  }

  function tegnTopp() {
    var naa = new Date();
    document.getElementById('klokke').textContent = pad(naa.getHours()) + ':' + pad(naa.getMinutes());
    var opptatt = 0, rode = 0;
    data.bord.forEach(function (b) {
      if (b.opptatt) { opptatt++; if (fargeFor(minutterSiden(b)) === 'rod') rode++; }
    });
    document.getElementById('oppsummering').innerHTML =
      '<b>' + opptatt + '</b> av ' + data.bord.length + ' opptatt' +
      (rode ? ' · <b class="tall-rod">' + rode + '</b> trenger besøk' : '');
    var s = data.innstillinger;
    document.getElementById('forklaring').innerHTML =
      '<span><i style="background:var(--gronn)"></i>under ' + s.gul + ' min</span>' +
      '<span><i style="background:var(--gul)"></i>' + s.gul + '–' + s.rod + ' min</span>' +
      '<span><i style="background:var(--rod)"></i>over ' + s.rod + ' min</span>' +
      '<span><i style="background:var(--ledig)"></i>ledig</span>';
  }

  function blink(id) {
    var el = elementer[id];
    if (!el) return;
    el.classList.remove('blink');
    void el.offsetWidth;
    el.classList.add('blink');
    setTimeout(function () { el.classList.remove('blink'); }, 600);
  }

  // Oppdater tiden: like etter hvert minuttskifte, og når appen kommer fram igjen
  function planleggTikk() {
    var ms = 60000 - (Date.now() % 60000) + 200;
    setTimeout(function () { tegn(); planleggTikk(); }, ms);
  }
  document.addEventListener('visibilitychange', function () {
    if (!document.hidden) { tegn(); holdVaken(); }
  });
  window.addEventListener('resize', tegn);
  window.addEventListener('orientationchange', function () { setTimeout(tegn, 300); });

  // ---------- Trykk, langt trykk og dra ----------
  var peker = null; // { id, el, startX, startY, timer, langt, flyttet, startBordX, startBordY }

  gulv.addEventListener('pointerdown', function (e) {
    var el = e.target.closest('.bord');
    if (!el) {
      if (redigerer) velgBord(null);
      return;
    }
    if (peker) return; // bare én finger om gangen
    e.preventDefault();
    var b = finnBord(el.dataset.id);
    if (!b) return;
    try { el.setPointerCapture(e.pointerId); } catch (x) { /* ignorer */ }
    peker = {
      pointerId: e.pointerId, id: b.id, el: el,
      startX: e.clientX, startY: e.clientY,
      startBordX: b.x, startBordY: b.y,
      langt: false, flyttet: false, timer: null
    };
    el.classList.add('trykket');
    if (!redigerer) {
      peker.timer = setTimeout(function () {
        if (!peker) return;
        peker.langt = true;
        el.classList.remove('trykket');
        if (navigator.vibrate) navigator.vibrate(30);
        visBordmeny(b);
      }, LANGT_TRYKK_MS);
    }
  });

  gulv.addEventListener('pointermove', function (e) {
    if (!peker || e.pointerId !== peker.pointerId) return;
    var dx = e.clientX - peker.startX, dy = e.clientY - peker.startY;
    if (!peker.flyttet && Math.hypot(dx, dy) > FLYTT_TOLERANSE) {
      peker.flyttet = true;
      clearTimeout(peker.timer);
      peker.el.classList.remove('trykket');
      if (redigerer) { velgBord(peker.id); peker.el.classList.add('drar'); }
    }
    if (redigerer && peker.flyttet) {
      var b = finnBord(peker.id);
      var r = gulv.getBoundingClientRect();
      var halv = bordStorrelsePx(b) / 2;
      var minX = halv / r.width * 100, minY = halv / r.height * 100;
      var nx = peker.startBordX + dx / r.width * 100;
      var ny = peker.startBordY + dy / r.height * 100;
      nx = Math.round(nx * 2) / 2; ny = Math.round(ny * 2) / 2; // fest til halve prosent
      b.x = Math.min(100 - minX, Math.max(minX, nx));
      b.y = Math.min(100 - minY, Math.max(minY, ny));
      peker.el.style.left = b.x + '%';
      peker.el.style.top = b.y + '%';
    }
  });

  function slippPeker(e, avbrutt) {
    if (!peker || e.pointerId !== peker.pointerId) return;
    var p = peker;
    peker = null;
    clearTimeout(p.timer);
    p.el.classList.remove('trykket', 'drar');
    var b = finnBord(p.id);
    if (!b) return;
    if (redigerer) {
      if (p.flyttet) lagre();
      else if (!avbrutt) velgBord(b.id);
      tegn();
      return;
    }
    if (!avbrutt && !p.langt && !p.flyttet) besokt(b);
  }
  gulv.addEventListener('pointerup', function (e) { slippPeker(e, false); });
  gulv.addEventListener('pointercancel', function (e) { slippPeker(e, true); });
  gulv.addEventListener('contextmenu', function (e) { e.preventDefault(); });

  // Hindre zoom med to fingre i Safari
  ['gesturestart', 'gesturechange', 'gestureend'].forEach(function (t) {
    document.addEventListener(t, function (e) { e.preventDefault(); }, { passive: false });
  });
  // Dobbelttrykk-zoom er slått av med «touch-action: manipulation» i CSS.

  // ---------- Dialog ----------
  var dialogBakgrunn = document.getElementById('dialog-bakgrunn');
  var dialog = document.getElementById('dialog');
  var dialogLukket = null;

  function apneDialog(html, vedLukk) {
    dialog.innerHTML = html;
    dialogBakgrunn.hidden = false;
    dialogLukket = vedLukk || null;
  }
  function lukkDialog() {
    dialogBakgrunn.hidden = true;
    dialog.innerHTML = '';
    var f = dialogLukket; dialogLukket = null;
    if (f) f();
  }
  dialogBakgrunn.addEventListener('pointerdown', function (e) {
    if (e.target === dialogBakgrunn) { e.preventDefault(); lukkDialog(); }
  });

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  // Langt trykk-meny
  function visBordmeny(b) {
    var min = minutterSiden(b);
    var status = min === null ? 'Ledig'
      : 'Opptatt · sist besøkt kl. ' + klokkeslett(b.sistBesok) + ' (' + min + ' min siden)';
    var angreTekst = 'Angre siste trykk';
    if (b.angre) {
      angreTekst += b.angre.opptatt && b.angre.sistBesok
        ? ' (tilbake til kl. ' + klokkeslett(b.angre.sistBesok) + ')'
        : ' (tilbake til ledig)';
    }
    apneDialog(
      '<h2>Bord ' + esc(b.navn) + '</h2><p>' + status + '</p>' +
      '<div class="knapperad">' +
        '<button class="knapp knapp-primar" data-h="besokt">Besøkt nå</button>' +
        (b.opptatt
          ? '<button class="knapp" data-h="ledig">Sett ledig</button>'
          : '<button class="knapp" data-h="opptatt">Sett opptatt</button>') +
        '<button class="knapp" data-h="angre"' + (b.angre ? '' : ' disabled') + '>' + angreTekst + '</button>' +
        '<button class="knapp knapp-dempet" data-h="lukk">Lukk</button>' +
      '</div>'
    );
    dialog.onclick = function (e) {
      var k = e.target.closest('[data-h]');
      if (!k) return;
      var h = k.dataset.h;
      lukkDialog();
      if (h === 'besokt') besokt(b);
      else if (h === 'ledig') settOpptatt(b, false);
      else if (h === 'opptatt') settOpptatt(b, true);
      else if (h === 'angre') angre(b);
    };
  }

  // ---------- Angre-melding ----------
  var melding = document.getElementById('melding');
  var meldingTimer = null;
  var meldingBordId = null;
  function visMelding(tekst, bordId) {
    document.getElementById('melding-tekst').textContent = tekst;
    meldingBordId = bordId;
    melding.hidden = false;
    clearTimeout(meldingTimer);
    meldingTimer = setTimeout(skjulMelding, 5000);
  }
  function skjulMelding() { melding.hidden = true; meldingBordId = null; }
  document.getElementById('melding-angre').addEventListener('click', function () {
    var b = meldingBordId && finnBord(meldingBordId);
    if (b) angre(b);
    skjulMelding();
  });

  // ---------- PIN ----------
  function spørPin(tittel, nårRiktig, sjekk) {
    var inn = '';
    var taster = [1, 2, 3, 4, 5, 6, 7, 8, 9, '', 0, '⌫'];
    apneDialog(
      '<h2>' + tittel + '</h2><p>Skriv inn PIN-kode (4 siffer).</p>' +
      '<div class="pin-prikker"><i></i><i></i><i></i><i></i></div>' +
      '<div class="tastatur">' + taster.map(function (t) {
        return t === '' ? '<span></span>' : '<button type="button" data-t="' + t + '">' + t + '</button>';
      }).join('') + '</div>' +
      '<div class="knapperad" style="margin-top:14px"><button class="knapp knapp-dempet" data-avbryt>Avbryt</button></div>'
    );
    var prikker = dialog.querySelector('.pin-prikker');
    function oppdater() {
      prikker.querySelectorAll('i').forEach(function (p, i) { p.classList.toggle('fylt', i < inn.length); });
    }
    dialog.onclick = function (e) {
      if (e.target.closest('[data-avbryt]')) { lukkDialog(); return; }
      var k = e.target.closest('[data-t]');
      if (!k) return;
      var t = k.dataset.t;
      if (t === '⌫') inn = inn.slice(0, -1);
      else if (inn.length < 4) inn += t;
      oppdater();
      if (inn.length === 4) {
        var verdi = inn;
        if (!sjekk || sjekk(verdi)) {
          setTimeout(function () { lukkDialog(); nårRiktig(verdi); }, 120);
        } else {
          prikker.classList.remove('feil'); void prikker.offsetWidth; prikker.classList.add('feil');
          setTimeout(function () { inn = ''; oppdater(); }, 350);
        }
      }
    };
  }

  // ---------- Redigeringsmodus ----------
  var bordpanel = document.getElementById('bordpanel');
  var navnFelt = document.getElementById('bord-navn');

  function settRedigering(på) {
    redigerer = på;
    document.body.classList.toggle('rediger', på);
    document.getElementById('topp').hidden = på;
    document.getElementById('topp-rediger').hidden = !på;
    if (!på) { velgBord(null); lagre(); }
    skjulMelding();
    tegn();
  }

  document.getElementById('knapp-rediger').addEventListener('click', function () {
    spørPin('Redigeringsmodus', function () { settRedigering(true); },
      function (p) { return p === data.innstillinger.pin; });
  });
  document.getElementById('knapp-ferdig').addEventListener('click', function () { settRedigering(false); });

  function velgBord(id) {
    valgtId = id;
    var b = id && finnBord(id);
    if (!b) {
      valgtId = null;
      bordpanel.hidden = true;
      if (document.activeElement === navnFelt) navnFelt.blur();
    } else {
      bordpanel.hidden = false;
      bordpanel.classList.toggle('venstre', b.x > 55);
      if (document.activeElement !== navnFelt) navnFelt.value = b.navn;
      markerValg('bord-form', b.form);
      markerValg('bord-storrelse', b.storrelse);
    }
    tegn();
  }

  function markerValg(gruppeId, verdi) {
    document.querySelectorAll('#' + gruppeId + ' button').forEach(function (k) {
      k.classList.toggle('aktiv', k.dataset.verdi === verdi);
    });
  }

  navnFelt.addEventListener('input', function () {
    var b = finnBord(valgtId);
    if (!b) return;
    b.navn = navnFelt.value.trim() || '?';
    lagre(); tegn();
  });
  navnFelt.addEventListener('keydown', function (e) { if (e.key === 'Enter') navnFelt.blur(); });

  document.getElementById('bord-form').addEventListener('click', function (e) {
    var k = e.target.closest('button'); var b = finnBord(valgtId);
    if (!k || !b) return;
    b.form = k.dataset.verdi; markerValg('bord-form', b.form); lagre(); tegn();
  });
  document.getElementById('bord-storrelse').addEventListener('click', function (e) {
    var k = e.target.closest('button'); var b = finnBord(valgtId);
    if (!k || !b) return;
    b.storrelse = k.dataset.verdi; markerValg('bord-storrelse', b.storrelse);
    // hold bordet innenfor gulvet etter størrelsesendring
    var halvX = bordStorrelsePx(b) / 2 / gulv.clientWidth * 100;
    var halvY = bordStorrelsePx(b) / 2 / gulv.clientHeight * 100;
    b.x = Math.min(100 - halvX, Math.max(halvX, b.x));
    b.y = Math.min(100 - halvY, Math.max(halvY, b.y));
    lagre(); tegn();
  });
  document.getElementById('bord-lukk').addEventListener('click', function () { velgBord(null); });
  document.getElementById('bord-slett').addEventListener('click', function () {
    var b = finnBord(valgtId);
    if (!b) return;
    apneDialog(
      '<h2>Fjerne bord ' + esc(b.navn) + '?</h2><p>Bordet tas bort fra plantegningen.</p>' +
      '<div class="knapperad side"><button class="knapp" data-h="nei">Avbryt</button>' +
      '<button class="knapp knapp-fare" data-h="ja">Fjern</button></div>'
    );
    dialog.onclick = function (e) {
      var k = e.target.closest('[data-h]');
      if (!k) return;
      lukkDialog();
      if (k.dataset.h === 'ja') {
        data.bord = data.bord.filter(function (x) { return x.id !== b.id; });
        lagre(); velgBord(null);
      }
    };
  });

  document.getElementById('knapp-nytt-bord').addEventListener('click', function () {
    var hoyeste = 0;
    data.bord.forEach(function (b) { var n = parseInt(b.navn, 10); if (n > hoyeste) hoyeste = n; });
    // finn en ledig plass nær midten
    var x = 50, y = 50, forsok = 0;
    while (forsok < 40 && data.bord.some(function (b) { return Math.abs(b.x - x) < 8 && Math.abs(b.y - y) < 10; })) {
      forsok++;
      x = 15 + (forsok * 37) % 70;
      y = 15 + (forsok * 23) % 70;
    }
    var nytt = {
      id: nyId(), navn: String(hoyeste + 1), form: 'firkant', storrelse: 'M',
      x: x, y: y, opptatt: false, sistBesok: null, angre: null
    };
    data.bord.push(nytt);
    lagre();
    velgBord(nytt.id);
  });

  // ---------- Innstillinger ----------
  document.getElementById('knapp-innstillinger').addEventListener('click', visInnstillinger);

  function visInnstillinger() {
    velgBord(null);
    var s = data.innstillinger;
    var gul = s.gul, rod = s.rod;
    apneDialog(
      '<h2>Innstillinger</h2>' +
      '<div class="rad"><div class="etikett"><span class="fargeprikk" style="background:var(--gul)"></span>Gul etter<small>Grønn før dette</small></div>' +
        '<div class="stepper"><button data-s="gul" data-d="-1">−</button><output id="v-gul"></output><button data-s="gul" data-d="1">+</button></div></div>' +
      '<div class="rad"><div class="etikett"><span class="fargeprikk" style="background:var(--rod)"></span>Rød etter<small>Mer enn så mange minutter</small></div>' +
        '<div class="stepper"><button data-s="rod" data-d="-1">−</button><output id="v-rod"></output><button data-s="rod" data-d="1">+</button></div></div>' +
      '<div class="rad"><div class="etikett">PIN-kode<small>For redigeringsmodus</small></div>' +
        '<button class="knapp" data-h="pin">Endre PIN</button></div>' +
      '<div class="rad"><div class="etikett">Nullstill dagen<small>Alle bord blir ledige</small></div>' +
        '<button class="knapp knapp-fare" data-h="nullstill">Nullstill</button></div>' +
      '<div class="knapperad" style="margin-top:16px"><button class="knapp knapp-primar" data-h="lagre">Lagre</button></div>'
    );
    function vis() {
      dialog.querySelector('#v-gul').textContent = gul + ' min';
      dialog.querySelector('#v-rod').textContent = rod + ' min';
    }
    vis();
    dialog.onclick = function (e) {
      var st = e.target.closest('[data-s]');
      if (st) {
        var d = parseInt(st.dataset.d, 10);
        if (st.dataset.s === 'gul') { gul = Math.max(1, Math.min(rod - 1, gul + d)); }
        else { rod = Math.max(gul + 1, Math.min(180, rod + d)); }
        vis();
        return;
      }
      var k = e.target.closest('[data-h]');
      if (!k) return;
      var h = k.dataset.h;
      if (h === 'lagre') {
        s.gul = gul; s.rod = rod; lagre(); lukkDialog(); tegn();
      } else if (h === 'pin') {
        s.gul = gul; s.rod = rod; lagre();
        lukkDialog();
        spørPin('Ny PIN-kode', function (ny) {
          spørPin('Gjenta ny PIN', function () {
            s.pin = ny; lagre(); visInnstillinger();
          }, function (p) { return p === ny; });
        });
      } else if (h === 'nullstill') {
        s.gul = gul; s.rod = rod; lagre();
        bekreftNullstill();
      }
    };
  }

  function bekreftNullstill() {
    apneDialog(
      '<h2>Nullstille dagen?</h2><p>Alle bord settes som ledige, og all tid nullstilles. Plantegningen beholdes.</p>' +
      '<div class="knapperad side"><button class="knapp" data-h="nei">Avbryt</button>' +
      '<button class="knapp knapp-fare" data-h="ja">Nullstill</button></div>'
    );
    dialog.onclick = function (e) {
      var k = e.target.closest('[data-h]');
      if (!k) return;
      lukkDialog();
      if (k.dataset.h === 'ja') {
        data.bord.forEach(function (b) { b.opptatt = false; b.sistBesok = null; b.angre = null; });
        lagre(); tegn();
      } else visInnstillinger();
    };
  }

  // ---------- Hold skjermen våken ----------
  var vakeLas = null;
  function holdVaken() {
    if (!('wakeLock' in navigator) || document.hidden) return;
    if (vakeLas && !vakeLas.released) return;
    navigator.wakeLock.request('screen').then(function (las) {
      vakeLas = las;
      document.getElementById('vaken').hidden = false;
      las.addEventListener('release', function () {
        document.getElementById('vaken').hidden = true;
      });
    }).catch(function () { /* krever ofte et trykk først – prøver igjen ved neste trykk */ });
  }
  holdVaken();
  document.addEventListener('pointerdown', holdVaken, true);

  // ---------- Service worker ----------
  if ('serviceWorker' in navigator && location.protocol !== 'file:') {
    window.addEventListener('load', function () {
      navigator.serviceWorker.register('sw.js').catch(function () { /* frakoblet uten cache */ });
    });
  }

  tegn();
  planleggTikk();
})();
