import resource, signal, subprocess, sys, tempfile, textwrap, os, json, pickle

def run_user_code(py_code:str, df_pickle:bytes, config, workdir:str=None):
    cpu_limit = int(config.cpu_limit)
    mem_limit = int(config.mem_limit)
    timeout = int(config.timeout)

    def set_limits():
        try:
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit))
        except (ValueError, resource.error):
            pass
        try:
            resource.setrlimit(resource.RLIMIT_AS, (mem_limit, mem_limit))
        except (ValueError, resource.error):
            pass
        os.environ["NO_PROXY"] = "*"  # example: block unintended egress

    with tempfile.TemporaryDirectory(dir=workdir) as td:
        path = os.path.join(td, "user_code.py")
        df_path = os.path.join(td, "df.pickle")
        result_path = os.path.join(td, "result.pickle")
        
        with open(df_path, "wb") as f:
            f.write(df_pickle)

        # prepend guards and data loading
        guarded_code = f"""import builtins
import sys

original_import = builtins.__import__
blacklist = []

def secure_importer(name, globals=None, locals=None, fromlist=(), level=0):
    if name in blacklist:
        raise ImportError(f"Import of module '{{name}}' is not allowed.")
    
    module = original_import(name, globals, locals, fromlist, level)
    if name == 'subprocess':
        for attr in ['call', 'run', 'Popen', 'check_call', 'check_output']:
            if hasattr(module, attr):
                delattr(module, attr)
    elif name == 'shutil':
        for attr in ['move', 'copy', 'copy2', 'copyfile', 'copytree', 'rmtree', 'chown']:
            if hasattr(module, attr):
                delattr(module, attr)
    return module

builtins.__import__ = secure_importer
for x in []: delattr(builtins,x)

import pickle
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import uuid
import urllib.parse
import os

df = pickle.load(open('{df_path}', 'rb'))
plots_dir = '{td}'

# User code starts here
{py_code}
# User code ends here

# Save the result
if 'result' in locals():
    with open('{result_path}', 'wb') as f:
        pickle.dump(result, f)

# Save any plots
for i in plt.get_fignums():
    fig = plt.figure(i)
    plot_filename = f"plot_{{uuid.uuid4().hex}}.jpg"
    plot_filepath = os.path.join(plots_dir, plot_filename)
    fig.savefig(plot_filepath)
    plt.close(fig)
"""
        
        open(path,"w").write(guarded_code)
        
        p = subprocess.Popen([sys.executable, path],
                             preexec_fn=set_limits,
                             cwd=td,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            out, err = p.communicate(timeout=timeout)  # wall clock
        except subprocess.TimeoutExpired:
            p.kill()
            return {"ok":False, "error":"timeout"}
        
        if p.returncode == 0:
            result = None
            if os.path.exists(result_path):
                with open(result_path, 'rb') as f:
                    result = pickle.load(f)
            
            plots = [os.path.join(td, f) for f in os.listdir(td) if f.endswith('.jpg')]
            
            return {"ok":True, "out":out, "err":err, "result":result, "plots": plots}
        else:
            return {"ok":False, "out":out, "err":err}
