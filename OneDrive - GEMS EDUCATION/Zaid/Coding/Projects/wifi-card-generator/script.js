// DOM elements
const qrTarget = document.getElementById('qrcode');
const networkInput = document.getElementById('networkInput');
const passwordInput = document.getElementById('passwordInput');
const networkPrint = document.getElementById('networkPrint');
const passwordPrint = document.getElementById('passwordPrint');
const savePngBtn = document.getElementById('savePngBtn');
const savePdfBtn = document.getElementById('savePdfBtn');
const printBtn = document.getElementById('printBtn');

// Main update: updates QR and the print/plain text fields
function updateWifiCard() {
  const ssid = networkInput.value || '';
  const password = passwordInput.value || '';
  const wifiQRData = `WIFI:T:WPA;S:${ssid};P:${password};;`;
  qrTarget.innerHTML = "";
  new QRCode(qrTarget, {
    text: wifiQRData,
    width: 126,
    height: 126,
    correctLevel: QRCode.CorrectLevel.H
  });
  networkPrint.textContent = ssid;
  passwordPrint.textContent = password;
}

// Sync card on input change
networkInput.addEventListener('input', updateWifiCard);
passwordInput.addEventListener('input', updateWifiCard);

networkInput.addEventListener('change', updateWifiCard);
passwordInput.addEventListener('change', updateWifiCard);
networkInput.addEventListener('paste', updateWifiCard);
passwordInput.addEventListener('paste', updateWifiCard);

// Export/print logic
function hideButtons() {
  document.querySelector('.button-group').style.display = 'none';
}
function showButtons() {
  document.querySelector('.button-group').style.display = '';
}

// Save as PNG
savePngBtn.addEventListener('click', () => {
  hideButtons();
  setTimeout(() => {
    html2canvas(document.getElementById('wifiCard'), { backgroundColor: "#fff" })
      .then(canvas => {
        showButtons();
        const link = document.createElement('a');
        link.href = canvas.toDataURL("image/png");
        const filename = `Wi-Fi ${networkInput.value || "Card"}.png`
        link.download = filename;
        link.click();
      });
  }, 100);
});

// Save as PDF
savePdfBtn.addEventListener('click', () => {
  hideButtons();
  setTimeout(() => {
    html2canvas(document.getElementById('wifiCard'), { backgroundColor: "#fff", scale: 2 })
      .then(canvas => {
        showButtons();
        const { jsPDF } = window.jspdf;
        const pdf = new jsPDF("p", "mm", "a4");
        const pageWidth = pdf.internal.pageSize.getWidth();
        const imgProps = {
          width: canvas.width,
          height: canvas.height
        };
        const pdfWidth = Math.min(180, pageWidth - 20);
        const scale = pdfWidth / imgProps.width;
        const pdfHeight = imgProps.height * scale;
        const x = (pageWidth - pdfWidth) / 2;
        const y = 20;
        pdf.addImage(canvas.toDataURL("image/png"), "PNG", x, y, pdfWidth, pdfHeight);
        const fileName = `Wi-fi ${networkInput.value || "Card"}.pdf`;
        pdf.save(fileName);
      });
  }, 100);
});

// Print
printBtn.addEventListener('click', () => {
  hideButtons();
  setTimeout(() => {
    window.print();
    setTimeout(showButtons, 200);
  }, 100);
});

// Initialize
updateWifiCard();
