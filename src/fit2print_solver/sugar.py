import subprocess
def run_sugar(text):
    with open("tmp.sugar", "w") as f:
        f.write(text)
    result = subprocess.run("./sugar.sh tmp.sugar", shell=True, capture_output=True, text=True)
    return result.stdout