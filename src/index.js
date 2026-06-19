// TRAKT LUBELSKI 26 waste-collection bot — Cloudflare Worker.
//
// Webhook (instant) handles commands/buttons; a cron trigger sends the daily
// reminder at 20:00 Warsaw. Per-chat settings + reminder dedup live in KV (STATE).
// Secret: TG_BOT_TOKEN (Worker secret). No getUpdates/polling — Telegram pushes
// updates to POST /telegram.

// ===== config =====
const ADDRESS = "TRAKT LUBELSKI 26 04-870 Wawer";
const ADDRESS_POINT_ID = "27088875";
const DEFAULTS = { lang: "pl", scope: "due", days_before: 1 };
const MORNING_HOUR = 9; // Warsaw — morning reminder
const EVENING_HOUR = 19; // Warsaw — evening reminder
const TZ = "Europe/Warsaw";
const PID = "portalCKMjunkschedules_WAR_portalCKMjunkschedulesportlet_INSTANCE_o5AIb2mimbRJ";
const OC_URL = "https://warszawa19115.pl/harmonogramy-wywozu-odpadow";
const NO_DATE = "1900-01-01";

// ===== i18n =====
const LANGS = ["en", "ru", "uk", "pl"];
const DEFAULT_LANG = "pl";
const LANG_NAMES = { en: "English 🇬🇧", ru: "Русский 🇷🇺", uk: "Українська 🇺🇦", pl: "Polski 🇵🇱" };
const EMOJI = { OP: "📄", OS: "🍾", MT: "🧴", BK: "🍎", OZ: "🌳", BG: "🍽️", ZM: "🗑️", WG: "🛋️" };
const CATEGORIES = {
  OP: { en: "Paper", ru: "Бумага", uk: "Папір", pl: "Papier" },
  OS: { en: "Glass", ru: "Стекло", uk: "Скло", pl: "Szkło" },
  MT: { en: "Plastic", ru: "Пластик", uk: "Пластик", pl: "Plastik" },
  BK: { en: "Bio", ru: "Био", uk: "Біо", pl: "Bio" },
  OZ: { en: "Green", ru: "Зелёные", uk: "Зелені", pl: "Zielone" },
  BG: { en: "Gastro", ru: "Гастро", uk: "Гастро", pl: "Gastro" },
  ZM: { en: "Mixed", ru: "Смешанные", uk: "Змішані", pl: "Zmieszane" },
  WG: { en: "Bulky", ru: "Габаритные", uk: "Габаритні", pl: "Gabaryty" },
};
const STRINGS = {
  title: { en: "Waste collection", ru: "Вывоз мусора", uk: "Вивіз сміття", pl: "Wywóz odpadów" },
  no_data: { en: "No schedule data.", ru: "Нет данных в графике.", uk: "Немає даних у графіку.", pl: "Brak danych w harmonogramie." },
  today: { en: "today", ru: "сегодня", uk: "сьогодні", pl: "dzisiaj" },
  tomorrow: { en: "tomorrow", ru: "завтра", uk: "завтра", pl: "jutro" },
  passed: { en: "passed", ru: "прошло", uk: "минуло", pl: "minęło" },
  choose_lang: { en: "🌐 Choose language:", ru: "🌐 Выберите язык:", uk: "🌐 Оберіть мову:", pl: "🌐 Wybierz język:" },
  lang_set: { en: "✅ Language: English", ru: "✅ Язык: Русский", uk: "✅ Мова: Українська", pl: "✅ Język: Polski" },
  welcome: {
    en: "👋 I send the waste-collection schedule for TRAKT LUBELSKI 26.\n\n/next — schedule now\n/language — change language\n/settings — notification settings",
    ru: "👋 Присылаю график вывоза мусора для TRAKT LUBELSKI 26.\n\n/next — график сейчас\n/language — сменить язык\n/settings — настройки уведомлений",
    uk: "👋 Надсилаю графік вивозу сміття для TRAKT LUBELSKI 26.\n\n/next — графік зараз\n/language — змінити мову\n/settings — налаштування сповіщень",
    pl: "👋 Wysyłam harmonogram wywozu odpadów dla TRAKT LUBELSKI 26.\n\n/next — harmonogram teraz\n/language — zmień język\n/settings — ustawienia powiadomień",
  },
  settings_title: { en: "⚙️ Settings", ru: "⚙️ Настройки", uk: "⚙️ Налаштування", pl: "⚙️ Ustawienia" },
  opt_scope: { en: "Show in a notification:", ru: "Показывать в уведомлении:", uk: "Показувати в сповіщенні:", pl: "Pokaż w powiadomieniu:" },
  scope_all: { en: "All upcoming", ru: "Весь график", uk: "Весь графік", pl: "Cały harmonogram" },
  scope_due: { en: "Only due", ru: "Только ближайшее", uk: "Тільки найближче", pl: "Tylko nadchodzące" },
  opt_days: { en: "Notify days before:", ru: "Уведомлять за дней:", uk: "Сповіщати за днів:", pl: "Powiadom dni wcześniej:" },
  settings_saved: { en: "✅ Settings updated", ru: "✅ Настройки обновлены", uk: "✅ Налаштування оновлено", pl: "✅ Ustawienia zaktualizowane" },
  btn_schedule: { en: "📅 Schedule", ru: "📅 График", uk: "📅 Графік", pl: "📅 Harmonogram" },
  btn_language: { en: "🌐 Language", ru: "🌐 Язык", uk: "🌐 Мова", pl: "🌐 Język" },
  btn_settings: { en: "⚙️ Settings", ru: "⚙️ Настройки", uk: "⚙️ Налаштування", pl: "⚙️ Ustawienia" },
};
const DAY_OPTIONS = [1, 2, 3, 4, 5, 6, 7];

function norm(lang) {
  lang = (lang || "").trim().toLowerCase().slice(0, 2);
  return LANGS.includes(lang) ? lang : DEFAULT_LANG;
}
function t(key, lang) {
  lang = norm(lang);
  return STRINGS[key][lang] || STRINGS[key][DEFAULT_LANG];
}
function category(code, lang) {
  return (CATEGORIES[code] && CATEGORIES[code][norm(lang)]) || code;
}
function emoji(code) {
  return EMOJI[code] || "🗑️";
}
function pluralRu(n, one, few, many) {
  if (n % 100 >= 11 && n % 100 <= 14) return many;
  const l = n % 10;
  if (l === 1) return one;
  if (l >= 2 && l <= 4) return few;
  return many;
}
function when(days, lang) {
  lang = norm(lang);
  if (days < 0) return t("passed", lang);
  if (days === 0) return t("today", lang);
  if (days === 1) return t("tomorrow", lang);
  const n = days;
  if (lang === "ru") return `через ${n} ${pluralRu(n, "день", "дня", "дней")}`;
  if (lang === "uk") return `через ${n} ${pluralRu(n, "день", "дні", "днів")}`;
  if (lang === "pl") return `za ${n} dni`;
  return `in ${n} days`;
}
function actionFor(text) {
  text = (text || "").trim().toLowerCase();
  const map = { btn_schedule: "schedule", btn_language: "language", btn_settings: "settings" };
  for (const [key, act] of Object.entries(map)) {
    if (Object.values(STRINGS[key]).map((v) => v.toLowerCase()).includes(text)) return act;
  }
  return null;
}

// ===== time (Warsaw, DST-aware) =====
function warsawParts() {
  const f = new Intl.DateTimeFormat("en-CA", {
    timeZone: TZ, year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", hour12: false,
  });
  const p = Object.fromEntries(f.formatToParts(new Date()).map((x) => [x.type, x.value]));
  return { date: `${p.year}-${p.month}-${p.day}`, hour: parseInt(p.hour, 10) % 24 };
}
function daysUntil(dateStr, todayStr) {
  return Math.round((Date.parse(dateStr + "T00:00:00Z") - Date.parse(todayStr + "T00:00:00Z")) / 86400000);
}
function fmtDate(s) {
  const [y, m, d] = s.split("-");
  return `${d}.${m}.${y}`;
}

// ===== waste schedule =====
async function fetchSchedule() {
  const params = new URLSearchParams({
    p_p_id: PID,
    p_p_lifecycle: "2",
    p_p_resource_id: "ajaxResource",
    [`_${PID}_addressPointId`]: ADDRESS_POINT_ID,
  });
  const r = await fetch(`${OC_URL}?${params}`, {
    headers: { Accept: "application/json", "User-Agent": "trakt-lubelski-worker/1.0" },
  });
  const data = await r.json();
  const out = [];
  for (const block of data || []) {
    for (const e of block.harmonogramyZ || []) {
      const d = e.data;
      if (!d || d === NO_DATE) continue;
      out.push({ date: d, code: (e.frakcja && e.frakcja.id_frakcja) || "?" });
    }
  }
  out.sort((a, b) => (a.date < b.date ? -1 : 1));
  return out;
}
function select(schedule, scope, daysBefore) {
  if (scope !== "due") return schedule;
  const today = warsawParts().date;
  return schedule.filter((e) => {
    const d = daysUntil(e.date, today);
    return d >= 0 && d <= Number(daysBefore);
  });
}
function formatSchedule(schedule, lang) {
  lang = norm(lang);
  const today = warsawParts().date;
  const lines = [`♻️ <b>${t("title", lang)}</b>`, `📍 <i>${ADDRESS}</i>`, ""];
  if (!schedule.length) {
    lines.push(t("no_data", lang));
    return lines.join("\n");
  }
  for (const e of schedule) {
    const days = daysUntil(e.date, today);
    lines.push(`${emoji(e.code)} <b>${category(e.code, lang)}</b> — ${fmtDate(e.date)} (${when(days, lang)})`);
  }
  return lines.join("\n");
}

// ===== Telegram =====
async function tg(env, method, params) {
  const r = await fetch(`https://api.telegram.org/bot${env.TG_BOT_TOKEN}/${method}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  return r.json();
}
async function send(env, chatId, text, replyMarkup) {
  const p = { chat_id: chatId, text, parse_mode: "HTML", disable_web_page_preview: true };
  if (replyMarkup) p.reply_markup = replyMarkup;
  return tg(env, "sendMessage", p);
}

// ===== KV state =====
async function ensureChat(env, id) {
  const raw = await env.STATE.get(`chat:${id}`);
  if (!raw) {
    const c = { ...DEFAULTS };
    await env.STATE.put(`chat:${id}`, JSON.stringify(c));
    return c;
  }
  return { ...DEFAULTS, ...JSON.parse(raw) };
}
async function getChat(env, id) {
  const raw = await env.STATE.get(`chat:${id}`);
  return raw ? { ...DEFAULTS, ...JSON.parse(raw) } : { ...DEFAULTS };
}
async function setOpt(env, id, key, val) {
  const c = await getChat(env, id);
  c[key] = val;
  await env.STATE.put(`chat:${id}`, JSON.stringify(c));
}
async function allChats(env) {
  const list = await env.STATE.list({ prefix: "chat:" });
  return list.keys.map((k) => k.name.slice(5));
}

// ===== keyboards =====
function mainKeyboard(lang) {
  return {
    keyboard: [
      [{ text: t("btn_schedule", lang) }],
      [{ text: t("btn_language", lang) }, { text: t("btn_settings", lang) }],
    ],
    resize_keyboard: true,
  };
}
function langKeyboard() {
  const b = LANGS.map((c) => ({ text: LANG_NAMES[c], callback_data: "setlang:" + c }));
  return { inline_keyboard: [b.slice(0, 2), b.slice(2)] };
}
function settingsKeyboard(lang, scope, days) {
  const mark = (txt, on) => (on ? "✅ " : "") + txt;
  const rowScope = [
    { text: mark(t("scope_all", lang), scope === "all"), callback_data: "setscope:all" },
    { text: mark(t("scope_due", lang), scope === "due"), callback_data: "setscope:due" },
  ];
  const rowDays = DAY_OPTIONS.map((d) => ({ text: mark(String(d), Number(days) === d), callback_data: "setdays:" + d }));
  return { inline_keyboard: [rowScope, rowDays] };
}
function settingsText(lang, scope, days) {
  const sl = t(scope === "all" ? "scope_all" : "scope_due", lang);
  return `<b>${t("settings_title", lang)}</b>\n\n${t("opt_scope", lang)} <b>${sl}</b>\n${t("opt_days", lang)} <b>${days}</b>`;
}

// ===== update handling =====
async function handleMessage(env, msg) {
  const chat = msg.chat && msg.chat.id;
  if (!chat) return;
  const c = await ensureChat(env, chat);
  const lang = c.lang;
  const raw = (msg.text || "").trim();
  const text = raw.toLowerCase();
  const action = actionFor(raw);

  if (text.startsWith("/start")) {
    await send(env, chat, t("welcome", lang), mainKeyboard(lang));
    await send(env, chat, t("choose_lang", lang), langKeyboard());
  } else if (action === "language" || text.startsWith("/lang")) {
    await send(env, chat, t("choose_lang", lang), langKeyboard());
  } else if (action === "settings" || text.startsWith("/settings")) {
    await send(env, chat, settingsText(lang, c.scope, c.days_before), settingsKeyboard(lang, c.scope, c.days_before));
  } else if (action === "schedule" || text.startsWith("/next") || text.startsWith("/schedule")) {
    const sched = await fetchSchedule();
    await send(env, chat, formatSchedule(sched, lang), mainKeyboard(lang));
  } else {
    await send(env, chat, t("welcome", lang), mainKeyboard(lang));
  }
}
async function refreshSettings(env, chat, mid, cqId) {
  const c = await getChat(env, chat);
  await tg(env, "answerCallbackQuery", { callback_query_id: cqId, text: t("settings_saved", c.lang) });
  await tg(env, "editMessageText", {
    chat_id: chat, message_id: mid, parse_mode: "HTML",
    text: settingsText(c.lang, c.scope, c.days_before),
    reply_markup: settingsKeyboard(c.lang, c.scope, c.days_before),
  });
}
async function handleCallback(env, cq) {
  const data = cq.data || "";
  const chat = cq.message.chat.id;
  const mid = cq.message.message_id;
  await ensureChat(env, chat);
  if (data.startsWith("setlang:")) {
    const code = norm(data.split(":")[1]);
    await setOpt(env, chat, "lang", code);
    await tg(env, "answerCallbackQuery", { callback_query_id: cq.id });
    await send(env, chat, t("lang_set", code), mainKeyboard(code));
    const sched = await fetchSchedule();
    await send(env, chat, formatSchedule(sched, code));
  } else if (data.startsWith("setscope:")) {
    await setOpt(env, chat, "scope", data.split(":")[1]);
    await refreshSettings(env, chat, mid, cq.id);
  } else if (data.startsWith("setdays:")) {
    await setOpt(env, chat, "days_before", Number(data.split(":")[1]));
    await refreshSettings(env, chat, mid, cq.id);
  }
}
async function handleUpdate(env, update) {
  if (update.callback_query) return handleCallback(env, update.callback_query);
  if (update.message) return handleMessage(env, update.message);
}

// ===== daily reminder =====
async function pushAll(env) {
  const sched = await fetchSchedule();
  let chats = await allChats(env);
  if (!chats.length && env.TG_CHAT_ID) chats = [env.TG_CHAT_ID];
  let sent = 0;
  for (const chat of chats) {
    const c = await getChat(env, chat);
    const items = select(sched, c.scope, c.days_before);
    if (c.scope === "due" && !items.length) continue;
    await send(env, chat, formatSchedule(items, c.lang));
    sent++;
  }
  return sent;
}
async function runSlot(env, date, slot) {
  // send a slot's reminder at most once per day (deduped per slot)
  const key = `meta:reminder:${slot}`;
  if ((await env.STATE.get(key)) === date) return;
  await pushAll(env);
  await env.STATE.put(key, date);
}
async function maybeDaily(env) {
  const { date, hour } = warsawParts();
  if (hour >= MORNING_HOUR && hour < 12) await runSlot(env, date, "morning");
  if (hour >= EVENING_HOUR) await runSlot(env, date, "evening");
}

// ===== worker entrypoints =====
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (request.method === "POST" && url.pathname === "/telegram") {
      let update;
      try {
        update = await request.json();
      } catch {
        return new Response("bad request", { status: 400 });
      }
      ctx.waitUntil(handleUpdate(env, update).catch((e) => console.log("update error:", e)));
      return new Response("ok");
    }
    if (url.pathname === "/" || url.pathname === "/health") {
      return new Response("trakt-lubelski waste bot is up");
    }
    return new Response("not found", { status: 404 });
  },
  async scheduled(event, env, ctx) {
    ctx.waitUntil(maybeDaily(env).catch((e) => console.log("daily error:", e)));
  },
};
