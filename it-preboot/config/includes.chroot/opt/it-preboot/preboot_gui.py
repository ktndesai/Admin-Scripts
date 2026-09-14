#!/usr/bin/env python3
import json
import os
import re
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from urllib.request import urlopen

CONF = Path('/etc/it-preboot/preboot.conf')
SECRETS = Path('/etc/it-preboot/secrets.env')


def read_shell_kv(path):
    out = {}
    if not path.exists():
        return out
    for raw in path.read_text(errors='ignore').splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        v = v.strip().strip('"').strip("'")
        out[k.strip()] = v
    return out

CFG = read_shell_kv(CONF)
CFG.update(read_shell_kv(SECRETS))


def cmd(args, default='Unknown'):
    try:
        return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL).strip() or default
    except Exception:
        return default


def first_line(text):
    return text.splitlines()[0].strip() if text and text != 'Unknown' else 'Unknown'


def hardware_info():
    cpu = first_line(cmd(['lscpu']))
    model = cmd(['bash', '-lc', "lscpu | awk -F: '/Model name/{sub(/^ +/,\"\",$2); print $2; exit}'"])
    mem = cmd(['bash', '-lc', "free -h | awk '/^Mem:/{print $2}'"])
    manufacturer = cmd(['dmidecode', '-s', 'system-manufacturer']) if os.geteuid() == 0 else cmd(['sudo','dmidecode','-s','system-manufacturer'])
    product = cmd(['sudo','dmidecode','-s','system-product-name'])
    serial = cmd(['sudo','dmidecode','-s','system-serial-number'])
    disks = cmd(['lsblk','-d','-e','7,11','-o','NAME,SIZE,MODEL,TYPE'])
    ipaddr = cmd(['bash','-lc', "ip -4 -br addr show up | awk '$1!=" + '"lo"' + "{print $1 \" \" $3}'"])
    return {
        'CPU': model,
        'RAM': mem,
        'Manufacturer': manufacturer,
        'Model': product,
        'Serial': serial,
        'Disks': disks,
        'Network': ipaddr,
    }


def split_container_and_sas():
    base = CFG.get('AZURE_CONTAINER_URL','').strip()
    sas = CFG.get('AZURE_SAS_TOKEN','').strip().lstrip('?')
    if not base:
        raise RuntimeError('AZURE_CONTAINER_URL is not configured')
    return base.rstrip('/'), sas


def blob_url(blob):
    base, sas = split_container_and_sas()
    return f"{base}/{blob.lstrip('/')}" + (f"?{sas}" if sas else '')


def get_manifest():
    manifest_blob = CFG.get('AZURE_MANIFEST_BLOB','manifest.json')
    with urlopen(blob_url(manifest_blob), timeout=20) as r:
        return json.load(r)


def local_disks():
    rows = []
    raw = cmd(['lsblk','-J','-d','-e','7,11','-o','NAME,SIZE,MODEL,TYPE'], default='{}')
    try:
        for d in json.loads(raw).get('blockdevices',[]):
            if d.get('type') == 'disk':
                rows.append((d['name'], f"/dev/{d['name']}  {d.get('size','')}  {d.get('model') or ''}".strip()))
    except Exception:
        pass
    return rows


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(CFG.get('ENVIRONMENT_NAME','IT Preboot'))
        self.geometry('980x700')
        self.minsize(900, 620)
        self.configure(padx=28, pady=20)
        self.images = []
        self.disk_map = {}
        self.make_ui()
        self.refresh_hw()
        self.refresh_status()

    def make_ui(self):
        tk.Label(self, text=CFG.get('COMPANY_NAME','Your Company'), font=('Sans', 13)).pack(anchor='w')
        tk.Label(self, text=CFG.get('ENVIRONMENT_NAME','IT Preboot'), font=('Sans', 28, 'bold')).pack(anchor='w', pady=(0,12))

        self.hw = tk.Text(self, height=12, font=('Monospace', 11), state='disabled')
        self.hw.pack(fill='x')

        status = tk.Frame(self)
        status.pack(fill='x', pady=12)
        self.net_lbl = tk.Label(status, text='Network: checking...')
        self.net_lbl.pack(side='left', padx=(0,25))
        self.vpn_lbl = tk.Label(status, text='VPN: checking...')
        self.vpn_lbl.pack(side='left', padx=(0,25))
        self.azure_lbl = tk.Label(status, text='Azure: not tested')
        self.azure_lbl.pack(side='left')

        btns = tk.Frame(self)
        btns.pack(fill='both', expand=True)
        for text, func in [
            ('Connect Corporate VPN', self.connect_vpn),
            ('Disconnect VPN', self.disconnect_vpn),
            ('Deploy Azure Image', self.deploy_window),
            ('Refresh Hardware', self.refresh_hw),
            ('Advanced Clonezilla', lambda: self.term('sudo /usr/local/bin/preboot-clonezilla')),
            ('Terminal', lambda: subprocess.Popen(['xterm'])),
        ]:
            tk.Button(btns, text=text, command=func, height=2, width=28).pack(pady=5)

        foot = tk.Frame(self)
        foot.pack(fill='x', pady=(10,0))
        tk.Button(foot, text='Reboot', command=lambda: self.power('reboot')).pack(side='right', padx=5)
        tk.Button(foot, text='Shutdown', command=lambda: self.power('poweroff')).pack(side='right', padx=5)

    def set_hw(self, info):
        lines = [
            f"Manufacturer : {info['Manufacturer']}",
            f"Model        : {info['Model']}",
            f"Serial       : {info['Serial']}",
            f"CPU          : {info['CPU']}",
            f"RAM          : {info['RAM']}",
            "",
            "Disks:", info['Disks'], "", "Network:", info['Network']
        ]
        self.hw.configure(state='normal')
        self.hw.delete('1.0','end')
        self.hw.insert('1.0','\n'.join(lines))
        self.hw.configure(state='disabled')

    def refresh_hw(self):
        threading.Thread(target=lambda: self.after(0, self.set_hw, hardware_info()), daemon=True).start()

    def refresh_status(self):
        network = cmd(['bash','-lc', "ip route | grep -q '^default ' && echo Connected || echo Disconnected"])
        self.net_lbl.config(text=f'Network: {network}')
        name = CFG.get('VPN_CONNECTION_NAME','Corporate L2TP')
        vpn = cmd(['bash','-lc', f"nmcli -t -f NAME connection show --active | grep -Fx {shlex_quote(name)} >/dev/null && echo Connected || echo Disconnected"])
        self.vpn_lbl.config(text=f'VPN: {vpn}')
        self.after(5000, self.refresh_status)

    def connect_vpn(self):
        self.term('sudo /usr/local/bin/preboot-vpn-connect; echo; read -p "Press Enter to close..."')

    def disconnect_vpn(self):
        subprocess.run(['sudo','/usr/local/bin/preboot-vpn-disconnect'])

    def term(self, shellcmd):
        subprocess.Popen(['xterm','-fa','Monospace','-fs','11','-e','bash','-lc',shellcmd])

    def power(self, action):
        if messagebox.askyesno('Confirm', f'{action.capitalize()} this computer?'):
            subprocess.Popen(['sudo', action])

    def deploy_window(self):
        w = tk.Toplevel(self)
        w.title('Deploy Azure Image')
        w.geometry('820x520')
        tk.Label(w, text='Azure Clonezilla Images', font=('Sans',20,'bold')).pack(anchor='w', padx=20, pady=(18,8))
        status = tk.Label(w, text='Loading manifest...')
        status.pack(anchor='w', padx=20)

        image_combo = ttk.Combobox(w, state='readonly', width=80)
        image_combo.pack(padx=20, pady=12, fill='x')
        disk_combo = ttk.Combobox(w, state='readonly', width=80)
        disk_combo.pack(padx=20, pady=12, fill='x')

        disks = local_disks()
        self.disk_map = {label:name for name,label in disks}
        disk_combo['values'] = [label for _,label in disks]
        if disks: disk_combo.current(0)

        log = tk.Text(w, height=12, font=('Monospace',10))
        log.pack(padx=20, pady=8, fill='both', expand=True)

        def load_manifest():
            try:
                data = get_manifest()
                self.images = data.get('images',[])
                labels = [f"{x.get('name',x.get('id'))} — {x.get('description','')}" for x in self.images]
                def ok():
                    image_combo['values'] = labels
                    if labels: image_combo.current(0)
                    status.config(text=f'Azure: {len(labels)} image(s) available')
                    self.azure_lbl.config(text='Azure: Connected')
                self.after(0,ok)
            except Exception as e:
                self.after(0, lambda: status.config(text=f'Azure error: {e}'))

        def deploy():
            if image_combo.current() < 0 or not disk_combo.get():
                messagebox.showerror('Missing selection','Select an image and target disk.')
                return
            img = self.images[image_combo.current()]
            target = self.disk_map[disk_combo.get()]
            if not messagebox.askyesno('ERASE TARGET DISK', f"This will ultimately ERASE /dev/{target}.\n\nDownload {img.get('name')} and continue?"):
                return
            threading.Thread(target=lambda: download_then_restore(img, target), daemon=True).start()

        def write(msg):
            self.after(0, lambda: (log.insert('end',msg+'\n'), log.see('end')))

        def download_then_restore(img, target):
            try:
                cache_root = Path(CFG.get('IMAGE_CACHE_ROOT','/var/tmp/it-preboot-images'))
                cache_root.mkdir(parents=True, exist_ok=True)
                prefix = img['blob_prefix'].strip('/')
                image_name = img.get('clonezilla_image') or Path(prefix).name
                dest_parent = cache_root
                base, sas = split_container_and_sas()
                source = f"{base}/{prefix}" + (f"?{sas}" if sas else '')
                write(f'Downloading {source.split("?")[0]} ...')
                p = subprocess.run(['azcopy','copy',source,str(dest_parent),'--recursive=true'], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                write(p.stdout)
                if p.returncode != 0:
                    raise RuntimeError('AzCopy download failed')
                image_dir = dest_parent / image_name
                if not image_dir.exists():
                    # AzCopy may preserve a prefix folder using its final path component.
                    candidates = list(dest_parent.glob(image_name))
                    if candidates: image_dir = candidates[0]
                if not image_dir.exists():
                    raise RuntimeError(f'Download finished but Clonezilla image directory was not found: {image_dir}')
                sums = img.get('sha256_manifest')
                if sums and (image_dir / sums).exists():
                    write('Verifying SHA256SUMS ...')
                    v = subprocess.run(['sha256sum','-c',sums], cwd=image_dir, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    write(v.stdout)
                    if v.returncode != 0: raise RuntimeError('Checksum verification failed')
                write('Download complete. Opening protected Clonezilla restore terminal...')
                self.after(0, lambda: self.term(f"sudo /usr/local/bin/preboot-restore-image {shell_quote(str(image_dir))} {shell_quote('/dev/'+target)}"))
            except Exception as e:
                write(f'ERROR: {e}')

        tk.Button(w, text='Download & Restore', command=deploy, height=2).pack(pady=10)
        threading.Thread(target=load_manifest, daemon=True).start()


def shell_quote(s):
    return "'" + str(s).replace("'", "'\\''") + "'"

def shlex_quote(s):
    return shell_quote(s)

if __name__ == '__main__':
    App().mainloop()
