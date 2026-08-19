import os
import re

filepath = r'c:\Users\LENOVO\Documents\GitHub\brazilianmonk.github.io\pages\monasteries.html'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove the commented out block at the beginning of the file.
comment_pattern = re.compile(r'<!--\s*\n\s*Monastery: Wat Photisumpara.*?-->', re.DOTALL)
if comment_pattern.search(content):
    content = comment_pattern.sub('', content, count=1)
    print("Removed commented out block from the beginning.")
else:
    print("Warning: Comment block not matched by regex pattern!")

# 2. Modify the country select options
country_select_pattern = re.compile(r'(<select id="f-country">.*?</select>)', re.DOTALL)
match_country = country_select_pattern.search(content)
if match_country:
    country_block = match_country.group(1)
    new_countries = """\t<option value="Nepal">🇳🇵 Nepal</option>
        <option value="Singapore">🇸🇬 Singapore</option>
        <option value="Taiwan">🇹🇼 Taiwan</option>
        <option value="USA">🇺🇸 USA</option>
        <option value="Vietnam">🇻🇳 Vietnam</option>"""
    updated_country_block = re.sub(r'[\t ]*<option value="Nepal">🇳🇵 Nepal</option>', new_countries, country_block)
    content = content.replace(country_block, updated_country_block)
    print("Updated country select dropdown.")
else:
    print("Error: country select dropdown not found!")

# 3. Modify the language select options
lang_select_pattern = re.compile(r'(<select id="f-language">.*?</select>)', re.DOTALL)
match_lang = lang_select_pattern.search(content)
if match_lang:
    lang_block = match_lang.group(1)
    new_langs = """\t<option value="Khmer">Khmer</option>
        <option value="Malay">Malay</option>
        <option value="Nepali">Nepali</option>
        <option value="Vietnamese">Vietnamese</option>
        <option value="Pāli">Pāli</option>"""
    updated_lang_block = re.sub(r'[\t ]*<option value="Khmer">Khmer</option>', new_langs, lang_block)
    content = content.replace(lang_block, updated_lang_block)
    print("Updated language select dropdown.")
else:
    print("Error: language select dropdown not found!")

# 4. Modify existing International Institute of Theravada entry to prepend Silamandapa
old_iit = '<td><a class="mon-link" href="https://www.theravado.com/" target="_blank" rel="noopener">International Institute of Theravāda</a></td>'
new_iit = '<td><a class="mon-link" href="https://www.theravado.com/" target="_blank" rel="noopener">Sīlamaṇḍapa (International Institute of Theravāda)</a></td>'
if old_iit in content:
    content = content.replace(old_iit, new_iit)
    print("Renamed International Institute of Theravada.")
else:
    print("Warning: International Institute of Theravada not found in HTML!")

# 5. Modify existing Nandaka Vihara entry
old_nandaka = """        <tr
          data-country="Malaysia"
          data-language="English Chinese Burmese"
          data-focus="Meditation">
          <td><a class="mon-link" href="https://www.nandakavihara.org/home" target="_blank" rel="noopener">Nandaka Vihāra Meditation Center</a></td>
          <td class="country-cell"><span class="flag">🇲🇾</span>Malaysia</td>
          <td>
            <span class="tag tag-lang">English</span>
            <span class="tag tag-lang">Chinese</span>
            <span class="tag tag-lang">Burmese</span>
          </td>"""

new_nandaka = """        <tr
          data-country="Malaysia"
          data-language="English Malay Chinese Burmese"
          data-focus="Meditation">
          <td><a class="mon-link" href="https://www.nandakavihara.org/home" target="_blank" rel="noopener">Nandaka Vihāra Meditation Center</a></td>
          <td class="country-cell"><span class="flag">🇲🇾</span>Malaysia</td>
          <td>
            <span class="tag tag-lang">English</span>
            <span class="tag tag-lang">Malay</span>
            <span class="tag tag-lang">Chinese</span>
            <span class="tag tag-lang">Burmese</span>
          </td>"""

if old_nandaka in content:
    content = content.replace(old_nandaka, new_nandaka)
    print("Updated Nandaka Vihara Meditation Center languages.")
else:
    print("Warning: Nandaka Vihara block not matched exactly!")

# 6. Insert new entries under Myanmar (before Sri Lanka section header)
new_myanmar = """        <tr
          data-country="Myanmar"
          data-language="English Burmese"
          data-focus="Meditation Study">
          <td><a class="mon-link" href="https://www.paaukforestmonastery.org/" target="_blank" rel="noopener">Pa-Auk Tawya Forest Monastery</a></td>
          <td class="country-cell"><span class="flag">🇲🇲</span>Myanmar</td>
          <td>
            <span class="tag tag-lang">Burmese</span>
            <span class="tag tag-lang">English</span>
          </td>
          <td><span class="tag tag-focus">Meditation</span><span class="tag tag-focus">Study</span></td>
          <td>Mawlamyine. The central monastery and source of the Pa-Auk meditation system. Abbot: Pa-Auk Tawya Sayadaw. Samatha &amp; Vipassanā, Sīla–Samādhi–Paññā.</td>
        </tr>

        <tr
          data-country="Myanmar"
          data-language="English Thai Burmese"
          data-focus="Meditation">
          <td><a class="mon-link" href="https://hehopaauktawya.org/" target="_blank" rel="noopener">Heho Pa-Auk Tawya</a></td>
          <td class="country-cell"><span class="flag">🇲🇲</span>Myanmar</td>
          <td>
            <span class="tag tag-lang">English</span>
            <span class="tag tag-lang">Thai</span>
            <span class="tag tag-lang">Burmese</span>
          </td>
          <td><span class="tag tag-focus">Meditation</span></td>
          <td>Heho. Teacher: Ven. Myanmar Revata. Meditation System: Pa-Auk.</td>
        </tr>

        <tr
          data-country="Myanmar"
          data-language="English Burmese"
          data-focus="Meditation">
          <td><a class="mon-link" href="https://pa-auktawyathanlyin.pamcmm.org/en/" target="_blank" rel="noopener">International Buddhasāsana Meditation Centre</a></td>
          <td class="country-cell"><span class="flag">🇲🇲</span>Myanmar</td>
          <td>
            <span class="tag tag-lang">Burmese</span>
            <span class="tag tag-lang">English</span>
          </td>
          <td><span class="tag tag-focus">Meditation</span></td>
          <td>Thanlyin. Ye-Oo Sayadaw / resident meditation teachers. Short- and longer-term practice.</td>
        </tr>

        <!-- ── Sri Lanka ── -->"""

content = content.replace('        <!-- ── Sri Lanka ── -->', new_myanmar)

# 7. Insert new entries under Sri Lanka (before Thailand section header)
new_sri_lanka = """        <tr
          data-country="Sri Lanka"
          data-language="Chinese English"
          data-focus="Meditation">
          <td>Muttidāya</td>
          <td class="country-cell"><span class="flag">🇱🇰</span>Sri Lanka</td>
          <td>
            <span class="tag tag-lang">Chinese</span>
            <span class="tag tag-lang">English</span>
          </td>
          <td><span class="tag tag-focus">Meditation</span></td>
          <td>Teacher: Ven. PRC Dhammañāṇa. Meditation System: Pa-Auk.</td>
        </tr>

        <tr
          data-country="Sri Lanka"
          data-language="Sinhala English Pāli"
          data-focus="Meditation">
          <td>Dhammika Ashrama</td>
          <td class="country-cell"><span class="flag">🇱🇰</span>Sri Lanka</td>
          <td>
            <span class="tag tag-lang">Sinhala</span>
            <span class="tag tag-lang">English</span>
            <span class="tag tag-lang">Pāli</span>
          </td>
          <td><span class="tag tag-focus">Meditation</span></td>
          <td>Resident nuns/teachers. Nuns' monastery.</td>
        </tr>

        <!-- ── Thailand ── -->"""

content = content.replace('        <!-- ── Thailand ── -->', new_sri_lanka)

# 8. Insert new entries under Thailand (before Laos section header)
new_thailand = """        <tr
          data-country="Thailand"
          data-language="Thai English"
          data-focus="Meditation">
          <td><a class="mon-link" href="https://www.paaukthailand.org/en/home-en/" target="_blank" rel="noopener">Angthong International Meditation Center</a></td>
          <td class="country-cell"><span class="flag">🇹🇭</span>Thailand</td>
          <td>
            <span class="tag tag-lang">Thai</span>
            <span class="tag tag-lang">English</span>
          </td>
          <td><span class="tag tag-focus">Meditation</span></td>
          <td>Angthong. Teachers: Ven. Myanmar Revata, Ven. Thai Bodhiñāṇa (Phra Ruj). Meditation System: Pa-Auk.</td>
        </tr>

\t<!-- ── Laos ── -->"""

content = content.replace('\t<!-- ── Laos ── -->', new_thailand)

# 9. Insert new entries under Laos (before Cambodia section header)
new_laos = """        <tr
          data-country="Laos"
          data-language="Lao Thai"
          data-focus="">
          <td><a class="mon-link" href="https://www.google.com/maps/place/Wat+Photisumpara/@18.0750722,102.8983233,674m/data=!3m2!1e3!4b1!4m6!3m5!1s0x3124f3b241953597:0x63033b8207eef270!8m2!3d18.0750722!4d102.8983233!16s%2Fg%2F11lkf8w27d!18m1!1e1?entry=ttu" target="_blank" rel="noopener">Wat Photisumpara (Bodhisambhāra)</a></td>
          <td class="country-cell"><span class="flag">🇱🇦</span>Laos</td>
          <td>
            <span class="tag tag-lang">Lao</span>
            <span class="tag tag-lang">Thai</span>
          </td>
          <td>—</td>
          <td>Ban Woen. Teacher: Ajahn Lao Nāgo. <a class="mon-link" href="https://www.google.com/maps/place/Wat+Photisumpara/@18.0750722,102.8983233,674m/data=!3m2!1e3!4b1!4m6!3m5!1s0x3124f3b241953597:0x63033b8207eef270!8m2!3d18.0750722!4d102.8983233!16s%2Fg%2F11lkf8w27d!18m1!1e1?entry=ttu" target="_blank" rel="noopener">Google Maps</a>.</td>
        </tr>

        <!-- ── Cambodia ── -->"""

content = content.replace('        <!-- ── Cambodia ── -->', new_laos)

# 10. Insert new entries under Malaysia (before Nepal section header)
new_malaysia = """        <tr
          data-country="Malaysia"
          data-language="English Malay Chinese Burmese"
          data-focus="Meditation">
          <td><a class="mon-link" href="https://www.nibbinda.org/" target="_blank" rel="noopener">Nibbinda Forest Monastery</a></td>
          <td class="country-cell"><span class="flag">🇲🇾</span>Malaysia</td>
          <td>
            <span class="tag tag-lang">English</span>
            <span class="tag tag-lang">Malay</span>
            <span class="tag tag-lang">Chinese</span>
            <span class="tag tag-lang">Burmese</span>
          </td>
          <td><span class="tag tag-focus">Meditation</span></td>
          <td>Penang. Resident Pa-Auk teachers. Forest meditation / Vipassanā.</td>
        </tr>

        <!-- ── Nepal ── -->"""

content = content.replace('        <!-- ── Nepal ── -->', new_malaysia)

# 11. Insert new entries under Nepal & add new country sections (Singapore, Taiwan, USA, Vietnam) before </tbody>
new_nepal_and_others = """        <tr
          data-country="Nepal"
          data-language="Nepali English Burmese"
          data-focus="Meditation">
          <td>Dhammadāyāda Pa-Auk Tawya Meditation Centre</td>
          <td class="country-cell"><span class="flag">🇳🇵</span>Nepal</td>
          <td>
            <span class="tag tag-lang">Nepali</span>
            <span class="tag tag-lang">English</span>
            <span class="tag tag-lang">Burmese</span>
          </td>
          <td><span class="tag tag-focus">Meditation</span></td>
          <td>Dolakha. Resident Pa-Auk teachers. Meditation and monastic practice.</td>
        </tr>

        <!-- ── Singapore ── -->
        <tr
          data-country="Singapore"
          data-language="English Chinese Burmese"
          data-focus="Meditation">
          <td><a class="mon-link" href="https://pamc.org.sg/" target="_blank" rel="noopener">Pa-Auk Meditation Centre</a></td>
          <td class="country-cell"><span class="flag">🇸🇬</span>Singapore</td>
          <td>
            <span class="tag tag-lang">English</span>
            <span class="tag tag-lang">Chinese</span>
            <span class="tag tag-lang">Burmese</span>
          </td>
          <td><span class="tag tag-focus">Meditation</span></td>
          <td>Resident Pa-Auk meditation teachers. Samatha &amp; Vipassanā meditation.</td>
        </tr>

        <tr
          data-country="Singapore"
          data-language="English Chinese Burmese"
          data-focus="Meditation">
          <td><a class="mon-link" href="https://www.visuddha-m-c.com/" target="_blank" rel="noopener">Visuddha Meditation Centre</a></td>
          <td class="country-cell"><span class="flag">🇸🇬</span>Singapore</td>
          <td>
            <span class="tag tag-lang">English</span>
            <span class="tag tag-lang">Chinese</span>
            <span class="tag tag-lang">Burmese</span>
          </td>
          <td><span class="tag tag-focus">Meditation</span></td>
          <td>Resident meditation teachers. Pa-Auk tradition.</td>
        </tr>

        <!-- ── Taiwan ── -->
        <tr
          data-country="Taiwan"
          data-language="Chinese English Burmese Pāli"
          data-focus="Study Meditation">
          <td><a class="mon-link" href="https://www.taiwandipa.org.tw/" target="_blank" rel="noopener">Taiwandīpa Theravāda Buddhist College (TIBC)</a></td>
          <td class="country-cell"><span class="flag">🇹🇼</span>Taiwan</td>
          <td>
            <span class="tag tag-lang">Chinese</span>
            <span class="tag tag-lang">English</span>
            <span class="tag tag-lang">Burmese</span>
            <span class="tag tag-lang">Pāli</span>
          </td>
          <td>
            <span class="tag tag-focus">Study</span>
            <span class="tag tag-focus">Meditation</span>
          </td>
          <td>Pa-Auk-trained monastic teachers. Theravāda education + meditation.</td>
        </tr>

        <tr
          data-country="Taiwan"
          data-language="Chinese English"
          data-focus="Meditation">
          <td><a class="mon-link" href="https://www.taiwandipa.org.tw/" target="_blank" rel="noopener">Samaṇasukhavana Forest Monastery</a></td>
          <td class="country-cell"><span class="flag">🇹🇼</span>Taiwan</td>
          <td>
            <span class="tag tag-lang">Chinese</span>
            <span class="tag tag-lang">English</span>
          </td>
          <td><span class="tag tag-focus">Meditation</span></td>
          <td>TIBC / Pa-Auk teachers. Forest meditation and monastic training.</td>
        </tr>

        <tr
          data-country="Taiwan"
          data-language="Chinese English"
          data-focus="Study Meditation">
          <td><a class="mon-link" href="https://www.taiwandipa.org.tw/" target="_blank" rel="noopener">Fa Zang Vihara</a></td>
          <td class="country-cell"><span class="flag">🇹🇼</span>Taiwan</td>
          <td>
            <span class="tag tag-lang">Chinese</span>
            <span class="tag tag-lang">English</span>
          </td>
          <td>
            <span class="tag tag-focus">Study</span>
            <span class="tag tag-focus">Meditation</span>
          </td>
          <td>Tainan. Pa-Auk/Taiwandipa teachers. Dhamma education and meditation.</td>
        </tr>

        <tr
          data-country="Taiwan"
          data-language="Chinese English"
          data-focus="Study">
          <td>Buddhist Hongshi College</td>
          <td class="country-cell"><span class="flag">🇹🇼</span>Taiwan</td>
          <td>
            <span class="tag tag-lang">Chinese</span>
            <span class="tag tag-lang">English</span>
          </td>
          <td><span class="tag tag-focus">Study</span></td>
          <td>Ven. Shih Shin Kuang and resident teachers. Buddhist education / study.</td>
        </tr>

        <!-- ── USA ── -->
        <tr
          data-country="USA"
          data-language="English"
          data-focus="Meditation">
          <td><a class="mon-link" href="https://www.americandhammasociety.org/" target="_blank" rel="noopener">Pa-Auk Tawya Vipassanā Dhura Hermitage</a></td>
          <td class="country-cell"><span class="flag">🇺🇸</span>USA</td>
          <td>
            <span class="tag tag-lang">English</span>
          </td>
          <td><span class="tag tag-focus">Meditation</span></td>
          <td>Georgia. Pa-Auk-trained meditation teachers. Vipassanā / meditation.</td>
        </tr>

        <tr
          data-country="USA"
          data-language="English"
          data-focus="Meditation">
          <td>Pa-Auk Tawya Saccadīpaka Vipassanā Centre</td>
          <td class="country-cell"><span class="flag">🇺🇸</span>USA</td>
          <td>
            <span class="tag tag-lang">English</span>
          </td>
          <td><span class="tag tag-focus">Meditation</span></td>
          <td>Southern California. Pa-Auk-trained teachers. Vipassanā meditation.</td>
        </tr>

        <!-- ── Vietnam ── -->
        <tr
          data-country="Vietnam"
          data-language="Vietnamese English Burmese"
          data-focus="Meditation">
          <td>Pa-Auk Tawya Vipassanā-Dhura Hermitage</td>
          <td class="country-cell"><span class="flag">🇻🇳</span>Vietnam</td>
          <td>
            <span class="tag tag-lang">Vietnamese</span>
            <span class="tag tag-lang">English</span>
            <span class="tag tag-lang">Burmese</span>
          </td>
          <td><span class="tag tag-focus">Meditation</span></td>
          <td>Dong Nai. Pa-Auk-trained teachers. Vipassanā / meditation.</td>
        </tr>

      </tbody>"""

content = content.replace('      </tbody>', new_nepal_and_others)
print("Added Nepal and other country sections.")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Modification complete.")
