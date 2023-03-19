document.getElementById('submit').addEventListener('click', async () => {
    const questionnaire = document.getElementById('questionnaire').value;
    const response = await fetch('/api/generate_answers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ questionnaire }),
    });
    const result = await response.json();
    if (result.success) {
        window.location.href = '/api/download_excel';
    } else {
        alert('生成回答失败，请重试。');
    }
});
