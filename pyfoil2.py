
# ██████  ██    ██ ███████  ██████  ██ ██      ██████
# ██   ██  ██  ██  ██      ██    ██ ██ ██           ██
# ██████    ████   █████   ██    ██ ██ ██       █████
# ██         ██    ██      ██    ██ ██ ██      ██
# ██         ██    ██       ██████  ██ ███████ ███████


import os, requests, zipfile, io, re, math
from os import path
from bs4 import BeautifulSoup
from heapq import nsmallest, nlargest

class foilscrape:
    def __init__(self, cd):
        self.cd = cd
        self.data_folder = cd + "\pyfoil_data\\"
        self.foil_datfolder = self.data_folder + "dat\\"
        self.foil_txtfolder = self.data_folder + "txt\\"
        self.solidworks_folder = self.data_folder + "solidworks_format\\"
        self.dat_list = []
        self.foil_list = []
        self.good_foil_list = []
        self.bad_foil_list = []
        self.misformated = []

        with open(self.cd + '\\blacklist.pyfoil', 'r') as blacklist:
            self.blacklist = [x for x in blacklist.read().splitlines()]
            self.bad_foil_list = list(set(self.bad_foil_list + self.blacklist))

        if not path.exists(self.data_folder):
            os.makedirs(self.data_folder)

        if not path.exists(self.foil_datfolder):
            os.makedirs(self.foil_datfolder)

        if not path.exists(self.foil_txtfolder):
            os.makedirs(self.foil_txtfolder)

        if not path.exists(self.solidworks_folder):
            os.makedirs(self.solidworks_folder)

        if path.isfile(self.data_folder + 'g.txt'):
            with open(self.data_folder + 'g.txt', 'r') as text:
                self.good_foil_list = [x for x in text.read().splitlines()]
                print('Loaded ' + str(len(self.good_foil_list)) + ' Foils')

        else:
            if not os.listdir(self.foil_datfolder):
                self._download_files()

            self.foil_list = self.get_foil_list()
            self.dat_list = self.get_dat_list()
            self._check_differences()

        if self._check_missing_txt():
            for a in self._check_missing_txt():
                if a not in self.blacklist:
                    print('Creating Text File: ' + a)
                    self._correct_txt(a, self._read_dat(a + '.dat'))
                    self.convert_to_solidworks(a, self._read_dat(a + '.dat'))

        self._write_good()

    def _download_files(self):
        url = "http://m-selig.ae.illinois.edu/ads/archives/coord_seligFmt.zip"
        data = requests.get(url, stream = True)
        unzip = zipfile.ZipFile(io.BytesIO(data.content))
        unzip.extractall(self.data_folder)
        orig_folder = self.data_folder + "coord_seligFmt\\"

        for x in os.listdir(orig_folder):
            os.rename(orig_folder + x, self.foil_datfolder + x)

        os.rmdir(orig_folder)

    def _check_differences(self):
        missing_files = list(set(self.foil_list)-set(self.dat_list))

        for x in missing_files if missing_files != None else None:
            with open(self.foil_datfolder + x + '.dat','w') as text:
                url = 'http://m-selig.ae.illinois.edu/ads/coord_seligFmt/'
                a = requests.get(url + x + '.dat')
                text.write(a.text)

    def _check_missing_txt(self):
        missing_files = list(set(self.foil_list)-set([x.split(
        '.')[0] for x in os.listdir(self.foil_txtfolder)]))

        return missing_files

    def _read_dat(self, filename):
        with open(self.foil_datfolder + filename, 'r', encoding = 'iso8859_15') as text:
            tocopy = []
            content = text.read().splitlines()

            for index, line in enumerate(content):
                if index == 0 and re.search('[a-zA-Z]', line):
                    continue

                if index == 1:
                    try:
                        q = float(line.split()[0])
                        w = float(line.split()[1])

                        if abs(q) > 1.5 and abs(w) > 1.5:
                            continue

                    except:
                        continue

                if line.count('.') > 2:
                    continue

                tocopy.append(line)

            if len(tocopy) > 10:
                return tocopy

            else:
                self.bad_foil_list.append(filename.split('.')[0])
                return False

    def _correct_txt(self, name, text):
        tocopy = []

        for line in text:
            s = line.split()

            self.misformated.append(name) if not text else None

            if len(s) < 2:
                continue

            if s[0][0] == '.' and name not in set(self.misformated):
                self.misformated.append(name)
                s[0] = '0' + s[0]

            elif s[0][0] == '-' and not s[0][1] == '0':
                if name not in set(self.misformated):
                    self.misformated.append(name)
                s[0] = '-0' + s[0][1::]

            if s[1][0] == '.' and name not in set(self.misformated):
                self.misformated.append(name)
                s[1] = '0' + s[1]

            elif s[1][0] == '-' and not s[1][1] == '0':
                if name not in set(self.misformated):
                    self.misformated.append(name)
                s[1] = '-0' + s[1][1::]

            if s[0][0] == '\(' and name not in set(self.misformated):
                self.misformated.append(name)
                s[0] = re.findall('(?<=\().+?(?=\))', s[0])

            if s[1][0] == '\(' and name not in set(self.misformated):
                self.misformated.append(name)
                s[1] = re.findall('(?<=\().+?(?=\))', s[1])

            tocopy.append(s[0] + ' ' + s[1])

        self.convert_to_txt(name, tocopy)

    def convert_to_solidworks(self, name, content):
            with open(self.solidworks_folder + name + '.txt', 'w') as text:
                for line in content:
                    text.write(line + '\t' + '0' + '\n')

    def _write_good(self):
        with open(self.data_folder + 'g.txt', 'w') as text:
            for x in os.listdir(self.foil_txtfolder):
                text.write(x.split('.')[0] + '\n')

    def convert_to_txt(self, name, tocopy):
        with open(self.foil_txtfolder + name + '.txt', 'w') as f:
            for line in tocopy:
                f.write(line.split()[0] + '\t' + line.split()[1] + '\n')
            self.good_foil_list.append(name)

    def get_foil_list(self):
        foil_list = []
        url = 'http://m-selig.ae.illinois.edu/ads/coord_seligFmt/'
        data = requests.get(url)
        soup = BeautifulSoup(data.text, 'lxml')
        tabl = soup.find('table')
        rows = tabl.find_all('tr')

        for row in rows:
            cols = row.find_all('td')
            cols = [ele.text.strip() for ele in cols]
            nam = cols[1].split('.')[0] if len(cols) == 5 else 'index'

            foil_list.append(nam) if nam != 'index' else None

        return foil_list[1::]

    def get_dat_list(self):
        return [x.split('.')[0] for x in os.listdir(self.foil_datfolder)]

    def get_path(self, name):
        return str(self.foil_txtfolder + name + '.txt')

class foil:
    def __init__(self, filepath, alpha, down):
        self.dir = filepath
        self.name = filepath.split('\\')[-1].split('.')[0]

        with open(self.dir, 'r') as text:
            self.lines = text.read().splitlines()
        self.increment_factor = len(self.lines)//2
        self.xy= [[float(x.split()[0]), float(x.split()[1])] for x in self.lines]

        if down == 1:
            alpha = -1 * alpha

        if alpha != 0:
            angle = (math.pi/180) * alpha
            newfoil = []

            for x in self.xy:
                px, py = x
                qx = math.cos(angle) * (px) - math.sin(angle) * (py)
                qy = math.sin(angle) * (px) + math.cos(angle) * (py)
                newfoil.append([qx,qy])

            self.xy = newfoil

        if down == 1:
            self.xy = [[x, -1* y] for [x,y] in self.xy]

        self.x = [x[0] for x in self.xy]
        self.y = [x[1] for x in self.xy]

        for index, x in enumerate(self.xy):
            if x == min(self.xy):
                self.top = self.xy[:index + 1]
                self.bottom = self.xy[index::]



class foilmath(foil):
    def __init__(self, scraper, name, alpha, down):
        self.scraper = scraper
        super().__init__(self.scraper.get_path(name), alpha, down)

    def calc_trailing_edge(self):
        return max(self.xy)

    def calc_leading_edge(self):
        return min(self.xy)

    def calc_le_gradient(self):
        closest = nlargest(4, self.xy, key=lambda g: abs(g[0] - 1))[2::]
        le = self.calc_leading_edge()

        if closest[0][1] > closest[1][1]:
            g1 = (le[1] - closest[0][1])/(le[0] - closest[0][0])
            g2 = (le[1] - closest[1][1])/(le[0] - closest[1][0])

        else:
            g1 = (le[1] - closest[1][1])/(le[0] - closest[1][0])
            g2 = (le[1] - closest[0][1])/(le[0] - closest[0][0])

        return([g1, g2])

    def calc_te_gradient(self):
        closest = nsmallest(4, self.xy, key=lambda g: abs(g[0] - 1))[2::]
        le = self.calc_leading_edge()

        if closest[0][1] > closest[1][1]:
            g1 = (le[1] - closest[0][1])/(le[0] - closest[0][0])
            g2 = (le[1] - closest[1][1])/(le[0] - closest[1][0])

        else:
            g1 = (le[1] - closest[1][1])/(le[0] - closest[1][0])
            g2 = (le[1] - closest[0][1])/(le[0] - closest[0][0])

        return([g1, g2])

    def calc_max_thickness(self):
        differences = []

        for x in range(self.increment_factor):
            incc = (x+1)*(1/self.increment_factor)
            closest = nsmallest(2, self.xy, key=lambda g: abs(g[0]- incc))
            differences.append([abs(closest[1][1] - closest[0][1]), incc])

        return max(differences)

    def calc_max_camber(self):
        camber = []

        for x in range(self.increment_factor):
            incc = (x+1)*(1/self.increment_factor)
            closest = nsmallest(2, self.xy, key=lambda g: abs(g[0]- incc))
            camber.append([0.5*(closest[1][1]+closest[0][1]), incc])

        return max(camber)

    def get_foil(self):
        return self.xy

scraper = foilscrape(path.dirname(path.realpath(__file__)))
