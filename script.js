const imageInput = document.getElementById('imageInput');
const origPreview = document.getElementById('origPreview');
const resultPreview = document.getElementById('resultPreview');
const processBtn = document.getElementById('processBtn');
const operationEl = document.getElementById('operation');
const keyEl = document.getElementById('key');
const modeEl = document.getElementById('mode');
const downloadLink = document.getElementById('downloadLink');


let currentFile = null;


imageInput.addEventListener('change', e => {
const f = e.target.files[0];
if (!f) return;
currentFile = f;
origPreview.src = URL.createObjectURL(f);
resultPreview.src = '';
downloadLink.style.display = 'none';
});


processBtn.addEventListener('click', async () => {
if (!currentFile) return alert('Please select an image first');
const key = keyEl.value || 'default';
const operation = operationEl.value;
const mode = modeEl.value; 


const fd = new FormData();
fd.append('image', currentFile);
fd.append('key', key);
fd.append('operation', operation);
fd.append('mode', mode);


processBtn.disabled = true;
processBtn.textContent = 'Processing...';
try {
const res = await fetch('/process', { method: 'POST', body: fd });
if (!res.ok) throw new Error('Server error');
const blob = await res.blob();
const url = URL.createObjectURL(blob);
resultPreview.src = url;
downloadLink.href = url;
downloadLink.style.display = 'inline-block';
} catch (err) {
alert('Error: ' + err.message);
} finally {
processBtn.disabled = false;
processBtn.textContent = 'Process';
}
});