const rewards = Array.isArray(window.REWARDS) ? window.REWARDS : [];

const allowedRewardHosts = new Set([
  "coin-master.co",
  "www.coin-master.co",
  "rewards.coinmaster.com",
  "coinmaster.onelink.me",
  "static.moonactive.net"
]);

function isVerifiedRewardUrl(value) {
  try {
    const parsed = new URL(value);
    return parsed.protocol === "https:" && allowedRewardHosts.has(parsed.hostname.toLowerCase());
  } catch {
    return false;
  }
}

const grid = document.querySelector("#rewards-grid");
const formatter = new Intl.DateTimeFormat("it-IT", { weekday: "long", day: "numeric", month: "long" });
const shortDateFormatter = new Intl.DateTimeFormat("it-IT", { day: "numeric", month: "long" });
document.querySelector("#today-label").textContent = formatter.format(new Date());
document.querySelector("#year").textContent = new Date().getFullYear();

const groupedRewards = rewards.reduce((groups, reward) => {
  if (!groups[reward.date]) groups[reward.date] = [];
  groups[reward.date].push(reward);
  return groups;
}, {});
const sortedDates = Object.keys(groupedRewards).sort().reverse();

sortedDates.forEach((date, dayIndex) => {
  const section = document.createElement("section");
  section.className = "reward-day";
  const readableDate = shortDateFormatter.format(new Date(`${date}T12:00:00`));
  const dayName = dayIndex === 0 ? "Oggi" : readableDate;
  const dateDetail = dayIndex === 0 ? `<span>${readableDate}</span>` : "";
  section.innerHTML = `<div class="reward-day__heading"><h3>${dayName}</h3>${dateDetail}</div><div class="rewards-grid"></div>`;
  const dayGrid = section.querySelector(".rewards-grid");

  groupedRewards[date].forEach((reward) => {
    const card = document.createElement("article");
    card.className = "reward-card";
    const hasLink = isVerifiedRewardUrl(reward.url);
    card.innerHTML = `
      <div class="reward-card__top">
        <span class="reward-icon" aria-hidden="true">🎁</span>
        <span class="reward-status">${hasLink ? "Disponibile" : "Non verificato"}</span>
      </div>
      <h3>${reward.title}</h3>
      <p>${readableDate} · Link Moon Active verificato</p>
      ${hasLink
        ? `<a class="button button--primary" href="${reward.url}" target="_blank" rel="noopener noreferrer nofollow">Riscatta premio ↗</a>`
        : `<button class="button button--disabled" type="button" disabled>Link non valido</button>`}
    `;
    dayGrid.appendChild(card);
  });
  grid.appendChild(section);
});

const toggle = document.querySelector("#theme-toggle");
const storedTheme = localStorage.getItem("spin-theme");
if (storedTheme === "dark") document.body.classList.add("dark");

function updateThemeButton() {
  const dark = document.body.classList.contains("dark");
  toggle.textContent = dark ? "☀" : "☾";
  toggle.setAttribute("aria-label", dark ? "Attiva tema chiaro" : "Attiva tema scuro");
}
updateThemeButton();

toggle.addEventListener("click", () => {
  document.body.classList.toggle("dark");
  localStorage.setItem("spin-theme", document.body.classList.contains("dark") ? "dark" : "light");
  updateThemeButton();
});
