"""Deterministic alternate-history command reserve; append-only to old leaders.

These are fictional academy cadres, not invented historical biographies. Use
the stock anonymous portrait rather than mislabelling a historical photograph.
Existing names, dates, ranks, skills, traits and pictures are byte-preserved.
"""
import argparse
import csv
import io
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROSTER = ROOT/'mod/db/leaders/india.csv'
FIRST_ID = 252000
TRAITS = {
    1:'logistics_wizard', 2:'defensive_doctrine', 4:'offensive_doctrine',
    8:'winter_specialist', 16:'trickster', 32:'engineer', 64:'fortress_buster',
    128:'panzer_leader', 256:'commando', 1024:'seawolf', 2048:'blockade_runner',
    4096:'superior_tactician', 8192:'spotter', 16384:'tank_buster',
    32768:'carpet_bomber', 65536:'night_flyer', 131072:'fleet_destroyer',
    262144:'desert_fox', 524288:'jungle_expert', 2097152:'forest_fighter',
    4194304:'mountain_expert', 8388608:'hills_fighter',
}
# Terrain trait spellings verified against the installed DH 1.05.2 parser
# strings; bit masks are from its bundled Leader Traits.txt.
PATTERNS = {
    0:(1|4, 2|32, 8|2, 128|4, 256|32, 256|4194304,
       524288|4, 8388608|32, 64|4, 262144|1, 2097152|2, 128|1),
    1:(1024, 1024|8192, 4096, 4096|8192, 2048|8192),
    2:(4096, 8192|4096, 131072, 131072|8192, 16384,
       16384|4096, 32768, 65536|32768),
}
# Fictional reserve officers need to read as people, not a Cartesian product.
# The services deliberately use different pools; no given name is used more
# than five times in the 375-officer reserve and every full name is unique.
LAND_GIVEN = (
    'Aditya','Ajit','Amar','Anand','Arjun','Baldev','Bikram','Chandra','Darshan','Devraj',
    'Dhirendra','Gopal','Harbaksh','Harinder','Harish','Jagat','Karan','Keshav','Kripal','Madhav',
    'Mahendra','Manek','Mohan','Nalin','Naresh','Pratap','Rajendra','Ranjit','Raghbir','Samar',
    'Shankar','Surendra','Tarun','Uday','Vikram','Zorawar','Aftab','Akhtar','Asghar','Bashir',
    'Farooq','Hamid','Iftikhar','Javed','Karim','Khalid','Latif','Mahmood','Nasir','Qadir',
    'Rashid','Salim','Tariq','Usman','Zafar','Ananth','Madhavan','Raghavan','Sundaram','Venkataraman')
LAND_FAMILY = (
    'Ahluwalia','Aiyar','Bakshi','Banerjee','Bedi','Bhagat','Bhalla','Bose','Chatterjee','Chaudhuri',
    'Dalvi','Dasgupta','Desai','Dhillon','Engineer','Ghosh','Gill','Jaffrey','Katoch','Kaul',
    'Khanna','Kohli','Kurup','Majumdar','Malhotra','Mankekar','Mathur','Menon','Mistry','Mukherji',
    'Nanda','Narang','Pandey','Panthaki','Qureshi','Raina','Rao','Reddy','Sabharwal','Sahni',
    'Samant','Sapru','Saran','Sethi','Shah','Siddiqi','Sinha','Sodhi','Talwar','Vohra',
    'Wadia','Zaidi','Zaman','Chakravarti','Dewan','Haksar','Iyengar','Lall','Mirza','Puri')
NAVAL_GIVEN = (
    'Behram','Cawas','Darius','Fali','Homi','Jal','Kaikobad','Minocher','Noshir','Rustom',
    'Sorab','Ardeshir','Dinshaw','Farid','Habib','Jamshed','Khurshid','Mansur','Nadir','Rehman',
    'Abhay','Arvind','Bhaskar','Deepak','Hemant','Inder','Kamal','Kiran','Madan','Nikhil',
    'Pramod','Ramesh','Sanjay','Subhash','Vijay','Ashfaq','Imtiaz','Naeem','Saeed','Yaqoob')
NAVAL_FAMILY = (
    'Avari','Balsara','Bharucha','Contractor','Daruwala','Dastur','Gandhi','Godrej','Irani','Katari',
    'Khandalavala','Kothari','Madon','Mody','Nadkarni','Patrawala','Soman','Tarapore','Vakil','Wacha',
    'Ansari','Baig','Chishti','Durrani','Faruqui','Habibullah','Ismail','Jalal','Kidwai','Lari',
    'Merchant','Mir','Naqvi','Rahman','Sami','Shamim','Sultan','Tyabji','Vazifdar','Warsi')
AIR_GIVEN = (
    'Abhinav','Ajoy','Akash','Anil','Arun','Avinash','Bharat','Chetan','Dilip','Gautam',
    'Girish','Indrajit','Jayant','Kailash','Krishan','Mahesh','Navin','Niranjan','Prakash','Prem',
    'Ravi','Roshan','Sachin','Satish','Shivdev','Sunil','Vasant','Vinod','Vishwanath','Yashwant',
    'Abbas','Adil','Faiz','Hasan','Iqbal','Jalal','Masood','Nawab','Rafiq','Shahid',
    'Tanvir','Waheed','Zahir','Aspy','Feroze','Minoo','Pesi','Rusi','Sam','Talyarkhan')
AIR_FAMILY = (
    'Agarwal','Ahuja','Badhwar','Bhandari','Chopra','Deol','Dutt','Gokhale','Grewal','Handa',
    'Jatar','Kapoor','Khosla','Luthra','Madan','Malik','Mehra','Naidu','Rajan','Sarin',
    'Sekhon','Suri','Thapar','Tuli','Varma','Bharadwaj','Chhibber','Datta','Dhingra','Ganguly',
    'Husain','Kazmi','Khatri','Mahajan','Nayar','Rizvi','Saigal','Saxena','Shukla','Sikand',
    'Bamji','Bhabha','Cursetji','Ghandy','Kanga','Maneckshaw','Poonawala','Siganporia','Tata','Wadia')
# 305 available by 1939, plus 70 graduates in 1944 for still larger campaigns.
WAVES = ((1933, (80,30,40)), (1936,(40,20,20)), (1939,(40,15,20)), (1944,(40,10,20)))


def reserve_name(branch, branch_number):
    given, family = ((LAND_GIVEN, LAND_FAMILY),
                     (NAVAL_GIVEN, NAVAL_FAMILY),
                     (AIR_GIVEN, AIR_FAMILY))[branch]
    # The second term changes the pairing after each complete pass through the
    # given-name pool. This prevents a later wave from recreating an old name.
    surname_index = (branch_number * 7 + (branch_number // len(given)) * 11) % len(family)
    return f'{given[branch_number % len(given)]} {family[surname_index]} (R)'


def reserve_rows():
    result=[]
    per_branch=Counter()
    for start, sizes in WAVES:
        for branch,count in enumerate(sizes):
            for _ in range(count):
                n=len(result); bn=per_branch[branch]; per_branch[branch]+=1
                name=reserve_name(branch,bn)
                # Mostly skill 2, one in three skill 3, no new skill 4+ stars.
                skill=3 if bn%3==0 else 2
                # Regular command ranks, with a smaller senior-command bench.
                # This edits no old rank. Broad seniority is earned over time.
                years=(start, start if bn%4 else start+3,
                       start+4 if bn%8==0 else 1990,
                       start+9 if bn%20==0 else 1990)
                result.append([name,str(FIRST_ID+n),'IND',*map(str,years),'2',
                    str(6 if skill==3 else 5),str(PATTERNS[branch][bn%len(PATTERNS[branch])]),
                    str(skill),'0','5',str(branch),'unknown',str(start),'1964','1999','x'])
    return result


def existing_prefix(raw):
    lines=raw.splitlines(keepends=True)
    first=next((n for n,l in enumerate(lines) if len(l.split(b';'))>1
        and l.split(b';')[1]==str(FIRST_ID).encode()),len(lines))
    tail=b''.join(lines[first:])
    if tail:
        ids={int(r[1]) for r in reserve_rows()}
        for line in tail.splitlines():
            if not line.strip():continue
            row=line.split(b';')
            if len(row)!=19 or not row[1].isdigit() or int(row[1]) not in ids:
                raise ValueError('Unrelated rows follow the reserved block; preserve and review them')
    return b''.join(lines[:first])


def apply_to_bytes(raw):
    prefix=existing_prefix(raw)
    lines=raw.splitlines(keepends=True)
    first=next((n for n,l in enumerate(lines) if len(l.split(b';'))>1
        and l.split(b';')[1]==str(FIRST_ID).encode()),len(lines))
    if first<len(lines):
        # Portrait tooling and later balance passes may legitimately change
        # columns in the generated block. Refresh names without destroying
        # those downstream changes.
        names={r[1]:r[0] for r in reserve_rows()}
        tail=[]
        for line in lines[first:]:
            ending=b'\r\n' if line.endswith(b'\r\n') else b'\n'
            row=line.rstrip(b'\r\n').split(b';')
            if len(row)>1 and row[1].decode('ascii') in names:
                row[0]=names[row[1].decode('ascii')].encode('ascii')
                line=b';'.join(row)+ending
            tail.append(line)
        return prefix+b''.join(tail)
    if not prefix.endswith(b'\n'):prefix+=b'\r\n'
    return prefix + ''.join(';'.join(r)+'\r\n' for r in reserve_rows()).encode('ascii')


def counts(raw,year):
    result=Counter()
    for r in csv.reader(io.StringIO(raw.decode('cp1252')),delimiter=';'):
        if len(r)<19 or not r[1].isdigit():continue
        if int(r[15])<=year<=int(r[16]):result[int(r[13])]+=1
    return dict(result)


def save_block(row, year, newline='\r\n'):
    years=list(map(int,row[3:7]))
    rank=min((3-i for i,y in enumerate(years) if y<=year),default=3)
    fields=[f'id = {{ type = 6 id = {row[1]} }}',f'name = "{row[0]}"',
        f'picture = "{row[14]}"',f'category = {("general","admiral","commander")[int(row[13])]}',
        f'rank = {rank}',*(f'y = {y}' for y in years),f'max_skill = {row[8]}',
        f'startyear = {row[15]}',f'ry = {row[17]}',f'skill = {row[10]}',
        *(f'trait = {name}' for bit,name in TRAITS.items() if int(row[9])&bit)]
    return newline+'\tleader = {'+newline+''.join('\t\t'+f+newline for f in fields)+'\t}'+newline


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    before=ROSTER.read_bytes();after=apply_to_bytes(before)
    if args.check:
        if before!=after:raise SystemExit('STALE: COMMAND-RESERVE1')
    else:ROSTER.write_bytes(after)
    print('COMMAND-RESERVE1', {y:counts(after,y) for y in (1933,1939,1941,1944)})


if __name__=='__main__':main()
