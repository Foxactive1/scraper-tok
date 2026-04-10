/**
 * app.js — InNovaIdeia / TikTok Scraper Pro
 * Frontend: scraping, polling de status, renderização e download de vídeos.
 */

let pollInterval = null;
let attempts     = 0;
const MAX_ATTEMPTS = 30; // 30 × 2s = 60 segundos

// Armazena URL do vídeo atual para o botão de download
let currentVideoUrl = "";

// ─── SCRAPING ────────────────────────────────────────────────────────────────

async function startScraping() {
    const urlInput = document.getElementById("url");
    const btn      = document.getElementById("btnScrape");
    const url      = urlInput.value.trim();

    if (!url) {
        showStatus("⚠️ Digite uma URL do TikTok antes de continuar.", "warning");
        return;
    }

    btn.disabled = true;
    showStatus("⏳ Enviando requisição...", "info");
    document.getElementById("result").innerHTML = "";
    document.getElementById("downloadArea").innerHTML = "";
    currentVideoUrl = "";
    attempts = 0;

    try {
        const response = await fetch("/scrape", {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ url }),
        });

        const data = await response.json();

        if (!response.ok) throw new Error(data.error || `Erro HTTP ${response.status}`);

        showStatus("⏳ Processando... aguarde.", "info");
        pollStatus(data.task_id, btn);

    } catch (error) {
        showStatus(`❌ ${escapeHtml(error.message)}`, "danger");
        btn.disabled = false;
    }
}

// ─── POLLING ─────────────────────────────────────────────────────────────────

async function pollStatus(taskId, btn) {
    if (pollInterval) clearInterval(pollInterval);

    pollInterval = setInterval(async () => {
        attempts++;

        if (attempts > MAX_ATTEMPTS) {
            clearInterval(pollInterval);
            showStatus("⏰ Tempo esgotado. Tente novamente.", "warning");
            btn.disabled = false;
            return;
        }

        showStatus(`⏳ Processando... (${attempts * 2}s / ${MAX_ATTEMPTS * 2}s)`, "info");

        try {
            const response = await fetch(`/status/${taskId}`);

            if (!response.ok) {
                clearInterval(pollInterval);
                showStatus(`❌ Erro ao consultar status (HTTP ${response.status})`, "danger");
                btn.disabled = false;
                return;
            }

            const data = await response.json();

            if (data.status === "SUCCESS") {
                clearInterval(pollInterval);
                renderResult(data.result);
                showStatus("✅ Dados extraídos com sucesso!", "success");
                btn.disabled = false;

            } else if (data.status === "FAILURE") {
                clearInterval(pollInterval);
                showStatus(`❌ Falha: ${escapeHtml(data.error || "Erro desconhecido")}`, "danger");
                btn.disabled = false;
            }

        } catch (error) {
            clearInterval(pollInterval);
            showStatus("❌ Erro de rede ao consultar status.", "danger");
            btn.disabled = false;
        }
    }, 2000);
}

// ─── RENDERIZAÇÃO ─────────────────────────────────────────────────────────────

function renderResult(data) {
    const container = document.getElementById("result");

    if (!data) {
        container.innerHTML = '<p class="text-center text-warning">Nenhum dado encontrado.</p>';
        return;
    }

    // Armazena URL para uso no download
    currentVideoUrl = data.video_url || "";

    container.innerHTML = `
        <div class="card bg-dark border border-secondary p-4 shadow">
            <h4 class="mb-1">@${escapeHtml(data.author)}</h4>
            <p class="text-secondary mb-3">${escapeHtml(data.desc)}</p>
            <div class="row text-center mb-3">
                <div class="col-6">
                    <h5 class="mb-0">${formatNumber(data.views)}</h5>
                    <small class="text-muted">👁 Views</small>
                </div>
                <div class="col-6">
                    <h5 class="mb-0">${formatNumber(data.likes)}</h5>
                    <small class="text-muted">❤️ Likes</small>
                </div>
            </div>
            <div class="d-grid gap-2">
                ${currentVideoUrl
                    ? `<a href="${escapeHtml(currentVideoUrl)}"
                          target="_blank" rel="noopener noreferrer"
                          class="btn btn-outline-light">
                           ▶ Ver no TikTok
                       </a>`
                    : ""
                }
                <button class="btn btn-warning" onclick="requestDownload()">
                    ⬇ Baixar Vídeo
                </button>
            </div>
        </div>
    `;
}

// ─── DOWNLOAD ─────────────────────────────────────────────────────────────────

async function requestDownload() {
    if (!currentVideoUrl) {
        showStatus("⚠️ Nenhum vídeo carregado. Faça o scraping primeiro.", "warning");
        return;
    }

    const btn = document.querySelector("button[onclick='requestDownload()']");
    if (btn) { btn.disabled = true; btn.textContent = "⏳ Obtendo link..."; }

    document.getElementById("downloadArea").innerHTML = "";

    try {
        const response = await fetch("/download", {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ url: currentVideoUrl }),
        });

        const data = await response.json();

        if (!response.ok) throw new Error(data.error || `Erro HTTP ${response.status}`);

        renderDownloadLinks(data);

    } catch (error) {
        showStatus(`❌ Download: ${escapeHtml(error.message)}`, "danger");
    } finally {
        if (btn) { btn.disabled = false; btn.textContent = "⬇ Baixar Vídeo"; }
    }
}

function renderDownloadLinks(links) {
    const area = document.getElementById("downloadArea");

    const makeBtn = (label, url, style) =>
        url
            ? `<a href="${escapeHtml(url)}"
                   download
                   target="_blank"
                   rel="noopener noreferrer"
                   class="btn ${style} w-100">
                   ${label}
               </a>`
            : "";

    area.innerHTML = `
        <div class="card bg-dark border border-warning p-3 mt-3 shadow">
            <h6 class="text-warning mb-3">⬇ Links de Download</h6>
            <div class="d-grid gap-2">
                ${makeBtn("📥 Sem marca d'água (HD)", links.url_hd, "btn-success")}
                ${makeBtn("📥 Sem marca d'água (SD)", links.url_sd, "btn-outline-success")}
                ${makeBtn("📥 Com marca d'água",      links.url_wm, "btn-outline-secondary")}
            </div>
            <small class="text-muted mt-2 d-block text-center">
                Links gerados via tikwm.com · expiram em alguns minutos
            </small>
        </div>
    `;
}

// ─── UTILITÁRIOS ──────────────────────────────────────────────────────────────

function showStatus(message, type = "info") {
    const el = document.getElementById("status");
    el.innerHTML = `<div class="alert alert-${type} text-center py-2 mb-0">${message}</div>`;
}

function formatNumber(num) {
    if (num === null || num === undefined) return "—";
    return new Intl.NumberFormat("pt-BR").format(num);
}

function escapeHtml(str) {
    if (!str) return "";
    const map = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" };
    return str.replace(/[&<>"']/g, (m) => map[m]);
}
