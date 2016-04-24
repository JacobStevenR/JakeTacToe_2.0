import sqlite3
import pickle
from operator import itemgetter

conn = sqlite3.connect("JTT2.db")
conn.text_factory = str
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("SELECT * FROM Chain")
r = cursor.fetchall()

items = []
for r in r:
    pos_patt_index = pickle.loads(r[0])
    resulting_patterns = pickle.loads(r[1])   
    times_chosen = r[2]
    top_patterns = r[3]

    
    items.append([pos_patt_index, resulting_patterns, times_chosen, top_patterns])

print len(items)
cursor.execute("SELECT patterns, total_game_patterns FROM winning_patterns")
winning_patterns_pkl = cursor.fetchone()
winning_patterns = pickle.loads(winning_patterns_pkl[0])
total_game_patterns = pickle.loads(winning_patterns_pkl[1])

f = open("JTT2.txt", "w+")
f.truncate()

f.write("Total_game_patterns:\n")
for tgp in total_game_patterns:
    f.write("%r\n" % tgp)

f.write("\nWinning Patterns:\n")
for w_p in winning_patterns:
    f.write("%r\n" % w_p)

for item in items:
    f.write("\n\n\n\n%r:\n\n" % item[0])
    f.write("Times Chosen: %r\n\n" % item[2])
    if item[3]:    
        f.write("Top Patterns: ")
        f.write(item[3])
        f.write("\n\n")    
    sorted_i = sorted(item[1], reverse=True, key=itemgetter(1))
    for x in sorted_i:
        f.write("%r\n" % x)
    f.write("\n\n\n\n")

f.close()
