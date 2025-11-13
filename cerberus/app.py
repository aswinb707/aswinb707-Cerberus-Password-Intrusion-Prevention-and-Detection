from flask import Flask, render_template, request, redirect, url_for
import textdistance
import time
app = Flask(__name__)

def damerau_levenshtein_similarity(s1, s2):
    dist = textdistance.damerau_levenshtein.distance(s1, s2)
    max_len = max(len(s1), len(s2))
    return 1 - dist / max_len if max_len else 1

def circular_edit_similarity(s1, s2):
    if not s2:
        return 1 if not s1 else 0
    best = 0
    for i in range(len(s2)):
        r = s2[i:] + s2[:i]
        dist = textdistance.levenshtein.distance(s1, r)
        sim = 1 - dist / max(len(s1), len(r))
        if sim > best:
            best = sim
    return best

def make_ngrams(s, n):
    if len(s) < n:
        return [s]
    return [s[i:i+n] for i in range(len(s) - n + 1)]

def ngram_cosine_similarity(s1, s2, n=3):
    g1 = make_ngrams(s1, n)
    g2 = make_ngrams(s2, n)
    return textdistance.cosine.similarity(g1, g2)

def hybrid_similarity(s1, s2, w1=0.4, w2=0.3, w3=0.3):
    s1, s2 = s1.lower(), s2.lower()
    sim1 = damerau_levenshtein_similarity(s1, s2)
    sim2 = circular_edit_similarity(s1, s2)
    sim3 = ngram_cosine_similarity(s1, s2)
    return round((w1 * sim1 + w2 * sim2 + w3 * sim3), 4)

original = "Aswin_0012"
TOO_DIFFERENT_THRESHOLD = 0.5
MAX_ABNORMAL = 3
MAX_WRONG = 10
LOCK_TIME = 100

abnormal_counter = 0
wrong_attempts = 0
abnormal_attempts = 0
locked_until = 0

@app.route('/', methods=['GET', 'POST'])
def login():
    global abnormal_counter, wrong_attempts, abnormal_attempts, locked_until

    message = None
    if time.time() < locked_until:
        remaining = int(locked_until - time.time())
        mins, secs = divmod(remaining, 60)
        return render_template("login.html", message=f"Locked for {mins:02d}:{secs:02d}")

    if request.method == 'POST':
        attempt = request.form['password']

        if attempt == original:
            return render_template("success.html",
                                   attempts=wrong_attempts + 1,
                                   abnormal=abnormal_attempts)

        sim = hybrid_similarity(original, attempt)

        if sim < TOO_DIFFERENT_THRESHOLD:
            abnormal_counter += 1
            abnormal_attempts += 1

        wrong_attempts += 1

        if abnormal_counter >= MAX_ABNORMAL:
            abnormal_counter = 0
            wrong_attempts = 0
            return redirect(url_for("loading_page"))

        elif wrong_attempts >= MAX_WRONG:
            locked_until = time.time() + LOCK_TIME
            message = f"Too many wrong attempts. Locked for {LOCK_TIME // 60} minute(s)."
        else:
            message = None  # no feedback for wrong password

    return render_template("login.html", message=message)

@app.route('/loading')
def loading_page():
    return render_template("loading.html")

if __name__ == "__main__":
    app.run(debug=True)
