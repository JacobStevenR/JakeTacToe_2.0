import random
import sqlite3
import pickle
from operator import itemgetter
from sys import argv
from collections import Counter

if __name__ == '__main__':
    script, repetitions = argv


class Engine(object):
    
    def __init__(self, player_x, player_o):
        
        self.grid = [["[ - ]" for x in range(0, 3)] for x in range(0, 3)]
        # Grid:
        # [
        #     [ - ] [ - ] [ - ],
        #     [ - ] [ - ] [ - ],
        #     [ - ] [ - ] [ - ],
        #                          ]   
        # Each cell is targeted with coordinates, eg. self.grid[y][x]

        self.winning_sets = [ [[0, 0], [1, 0], [2, 0]], [[0, 0], [0, 1], [0, 2]], [[0, 0], [1, 1], [2, 2]], [[0, 1], [1, 1], [2, 1]], 
        [[0, 2], [1, 1], [2, 0]], [[0, 2], [1, 2], [2, 2]], [[1, 0], [1, 1], [1, 2]], [[2, 0], [2, 1], [2, 2]], ]
        # A list of 3-item lists, each of the 3 items is a 2-item list of coordinates [x, y].  Each 3-itemlist signifies 3-in-a-row        
        
        self.available = [[0, 0], [0, 1], [0, 2], [1, 0], [1, 1], [1, 2], [2, 0], [2, 1], [2, 2]]
        # The coordinate for each space on grid.  Used to keep track of available moves

        self.player_x = player_x
        self.player_o = player_o
        # This attribute contains player class objects

      


    def reset_board(self):
        '''
        Resets the game board to it's original values so a new game can commence.
        '''
        del self.available[:]
        self.available = [[0, 0], [0, 1], [0, 2], [1, 0], [1, 1], [1, 2], [2, 0], [2, 1], [2, 2]]
        del self.grid[:]
        self.grid = [["[ - ]" for x in range(0, 3)] for x in range(0, 3)]


    def print_grid(self):
        '''
        Prints the grid in its current state
        '''
        for row in self.grid:
            for x in row:
                print x,
            print "\n"
        print "\n\n", 



    def check_for_win(self, player):
        '''
        Checks the squares owned by player against winning sets.  Returns True if player possesses all 3  of one of the winning sets
        '''
        match = 0

        for ws in self.winning_sets:
            for tup in player.owned:
                if tup in ws:
                    match += 1

            if match == 3:
                self.print_grid()
                print "%s is the winner!" % player.symbol
                return True

            else:
                match = 0

        return False



    def check_for_draw(self):
        '''
        If all available grid spaces have already been chosen, self.available will be empty signifying a draw.
        Returns True if there is a draw
        '''
        if self.available:
            return False
        else:
            print "DRAW!"
            return True


    def play_round(self, player, compete):
        '''
        This function called within Engine.play_game().  Accepts two arguments, player (the Engine.player attribute of the current player) 
        and a boolean which signifies whether position_pattern and index will be chosen randomly or if they will be chosen by the
        Player.compete() function.

        Once position_pattern and index have been determined, the matrix_index (a 2-item list which contains grid coordinates [x, y]) is
        determined by the Player.choose() function.

        This matrix_index is used to update the grid, the remove the chosen space from Engine.available, and to add the chosen space to
        Player.owned.

        Player.new_pattern_function() is used to produce a list of all new position_patterns which appeared after the move was made

        Finally, Player.update_chain() is called which keeps track of which moves lead to which new_patterns.
        This is explained in more detail within the Player.update_chain() function.
        '''
        player.tgp_function(self.grid)

        if compete:
            position_pattern, index = player.compete(self.grid)

        else:    
            position_pattern, index = player.random_move(player.validate(player.build_pattern_list(self.grid)))
            
        matrix_index = player.choose(position_pattern, index)
        
        self.grid[matrix_index[0]][matrix_index[1]] = self.grid[matrix_index[0]][matrix_index[1]].replace('-', player.symbol)
        self.available.remove(matrix_index)
        player.owned.append(matrix_index)

        new_patterns = player.new_pattern_function(self.grid)
        player.update_chain(position_pattern, index, new_patterns)
        

       

    def play_game(self):
        '''
        This function is responsible for initiating the game sequence.
        
        First, a database connection is opened for each player.

        Next is a set of initializing steps which set the Player.previous_layer, Player.new_patterns, and Player.total_game_patterns
        attributes.  


        Next a loop is initiated.  This loop will print the grid then call Engine.play_round() for player X.  Next it will call
        Engine.check_for_win to determine if player X wins.  If so, Player.find_winning_pos() is called,
        the database connections for each player is closed, and the function returns.
        If no win, Engine.check_for_draw() is called to determine if there is a draw. If so, the function returns.  If neither win nor draw,
        the same sequence commences for player O

        The loop continues until a win or draw.
        '''

        self.player_x.open_connection()
        self.player_o.open_connection()
        
        self.player_x.previous_layer = player_x.build_pattern_list(self.grid)
        for p_l in self.player_x.previous_layer:
            if p_l not in self.player_x.new_patterns:
                self.player_x.new_patterns.append(p_l)

        self.player_o.previous_layer = player_x.build_pattern_list(self.grid)
        for p_l in self.player_o.previous_layer:
            if p_l not in self.player_o.new_patterns:
                self.player_o.new_patterns.append(p_l)
        
        self.player_x.cursor.execute("SELECT total_game_patterns FROM winning_patterns")
        r = self.player_x.cursor.fetchone()
        if r:
            self.player_x.total_game_patterns = pickle.loads(r[0])
            

        self.player_o.cursor.execute("SELECT total_game_patterns FROM winning_patterns")
        r = self.player_o.cursor.fetchone()
        if r:
            self.player_o.total_game_patterns = pickle.loads(r[0])

        
        while True:
            self.print_grid()
            self.play_round(self.player_x, False)
            
            if self.check_for_win(self.player_x):
                self.player_x.find_winning_pos()
                self.player_x.close_connection()
                self.player_o.close_connection()
                return "X"
            elif self.check_for_draw():
                self.player_x.close_connection()
                self.player_o.close_connection()
                return "D"
            
            self.print_grid()
            self.play_round(self.player_o, False)
            if self.check_for_win(self.player_o):
                self.player_o.find_winning_pos()
                self.player_x.close_connection()
                self.player_o.close_connection()
                return "O"
            elif self.check_for_draw():
                self.player_x.close_connection()
                self.player_o.close_connection()
                return "D"




class Player(object):
    
    def __init__(self, symbol):
        self.symbol = symbol
        self.owned = []
        self.new_patterns = []
        self.total_game_patterns = []
        self.previous_layer = []
        
        

    def reset_player(self):
        del self.owned[:]
        del self.new_patterns[:]
        del self.total_game_patterns[:]
        del self.previous_layer



    def open_connection(self):
        '''
        Opens a Sqlite3 database connection.
        '''

        self.conn = sqlite3.connect("JTT2.db")
        
        self.conn.text_factory = str
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor() 

        self.cursor.execute('''CREATE TABLE if not exists Chain
            (pos_patt_index, resulting_patterns, times_chosen, top_patterns)''')
        
        self.cursor.execute('''CREATE TABLE if not exists winning_patterns
            (patterns, total_game_patterns)''')
               
        self.conn.commit()



    def close_connection(self):
        self.conn.close()


    def test_around(self, grid, y, x, symbol):
        """
        This function accepts a grid, y and x coordinates, and the Player.symbol attribute ("X", or "O").

        It checks the grid locations surrounding the location indicated by the y and x coordinates.  It returns a 4-item dictionary which
        contains keys 'horizontal', 'vertical', 'RLdiagonal', and 'LRdiagonal'. The values for each of these keys is
        a 3-item list which indicates the value of grid locations adjacent to the grid location indicated by the y and x coordinates.  
        For example, the 'horizontal' key's value specifies the value of the grid locations as follows: [left, center, right].  
        If the grid value is the same as the symbol argument '+' is appended to the 3-item list in the proper location.
        If it is unchosen, 'E' is appended.  If it doesn't exist, 'None' is appended.  And if it is none of the above, it
        is assumed it is the opposing player's symbol in which case a '-' is appended.

        In the end, it returns a dictionary for the grid location specified by the y and x coordinates of the form:
  
        { 
            'vertical' : ['E', 'E', '-'], 
            'horizontal' : ['None', 'E' '+'], 
            'LRdiagonal' : ['None','E' 'E'], 
            'RLdiagonal' : ['-', 'E', 'None'],
                                                   }

        The locations indicated by the 3-item list are as follows:

        { 
            'vertical' : [Above, Center, Below], 
            'horizontal' : [Left, Center Right], 
            'LRdiagonal' : [Upper-left, Center Lower-Right], 
            'RLdiagonal' : [Upper-Right, Center, Lower-Left],
                                                   }
        """
    
        vertical_length = len(grid)
        horizontal_length = len(grid[0])
   
        surround = {
        'main' : grid[y][x],
        'top_left' : None,
        'above' : None,
        'top_right' : None,
        'left' : None,
        'right' : None,
        'bottom_left' : None,
        'below' : None,
        'bottom_right' : None,
        }

        if y-1 < 0 and x-1 < 0:
            surround['right'] = grid[y][x+1]
            surround['below'] = grid[y+1][x]
            surround['bottom_right'] = grid[y+1][x+1]
 
        elif y-1 < 0 and x+1 >= horizontal_length:
            surround['left'] = grid[y][x-1]
            surround['bottom_left'] = grid[y+1][x-1]
            surround['below'] = grid[y+1][x]

        elif y+1 >= vertical_length and x-1 < 0:
            surround['above'] = grid[y-1][x]
            surround['top_right'] = grid[y-1][x+1]
            surround['right'] = grid[y][x+1]
       
        elif y+1 >= vertical_length and x+1 >= horizontal_length:
            surround['top_left'] = grid[y-1][x-1]
            surround['above'] = grid[y-1][x]
            surround['left'] = grid[y][x-1]
    
        elif y-1 < 0:
            surround['left'] = grid[y][x-1]
            surround['right'] = grid[y][x+1]
            surround['bottom_left'] = grid[y+1][x-1]
            surround['below'] = grid[y+1][x]
            surround['bottom_right'] = grid[y+1][x+1]

        elif x-1 < 0:
            surround['above'] = grid[y-1][x]
            surround['top_right'] = grid[y-1][x+1]
            surround['right'] = grid[y][x+1]
            surround['below'] = grid[y+1][x]
            surround['bottom_right'] = grid[y+1][x+1]

        elif y+1 >= vertical_length:
            surround['top_left'] = grid[y-1][x-1]
            surround['above'] = grid[y-1][x]
            surround['top_right'] = grid[y-1][x+1]
            surround['left'] = grid[y][x-1]
            surround['right'] = grid[y][x+1]
        
        elif x+1 >= horizontal_length:
            surround['top_left'] = grid[y-1][x-1]
            surround['above'] = grid[y-1][x]
            surround['left'] = grid[y][x-1]
            surround['bottom_left'] = grid[y+1][x-1]
            surround['below'] = grid[y+1][x]

        else:
            surround['top_left'] = grid[y-1][x-1]
            surround['above'] = grid[y-1][x]
            surround['top_right'] = grid[y-1][x+1]
            surround['left'] = grid[y][x-1]
            surround['right'] = grid[y][x+1]
            surround['bottom_left'] = grid[y+1][x-1]
            surround['below'] = grid[y+1][x]
            surround['bottom_right'] = grid[y+1][x+1]


        angles = {
    
        'vertical' : [surround['above'], surround['main'], surround['below']],
        'horizontal' : [surround['left'], surround['main'], surround['right']],
        'LRdiagonal' : [surround['top_left'], surround['main'], surround['bottom_right']],
        'RLdiagonal' : [surround['top_right'], surround['main'], surround['bottom_left']],
        } 

        for k, v in angles.iteritems():
            for x in range(0,3):
                if v[x] == "[ " + symbol + " ]": #If adjacent cell same as self
                    angles[k][x] = "+"
                elif v[x] == "[ - ]":
                    angles[k][x] = "E" # "E" for empty, if adjacent cell empty
                elif v[x] == None:
                    angles[k][x] = "None"
                else:
                    angles[k][x] = "-" # If adjacent cell different than self
    
        return angles




     
    def filterp(self, layer):
        '''
        Accepts a list as an argument

        Removes duplicate values from the list fed into it
        '''

        patterns = []
        for l in layer:
            if l not in patterns:
                patterns.append(l)
        return patterns



    def build_pattern_list(self, grid):
        '''
        Takes grid as an argument.
 
        Runs Player.test_around() for each grid coordinate.  Builds the dictionaries returned by Player.test_around()
        into 3 lists of various detail...called layers here.  For now, I only return layer_3 (see below).  But layer_1 and layer_2 can
        possibly be used later on for more general learning, so I'm keeping the functionality in place.

        See the internal comments for more detail.  
        '''

        test_around_result = []
        for y in range(0, 3):
            for x in range(0, 3):
                # test_around(), when called, returns a 4-item dict describing the horizontal, vertical, and both diagonal surroundings
                # of the coordinate fed to it
                test_around_result.append([[y, x], self.test_around(grid, y, x, self.symbol)])
                # test_around_result is a list of lists containing
                # coordinates [y, x] and the 4-item-dict returned from test_around() with those coordinates.
                # For example [[1, 1], {'horizontal' : ['E', 'E', 'E'], 'vertical' : ['E', 'E', 'E'],
                # 'LRdiagonal' : ['E', 'E', 'E'], 'RLdiagonal' : ['E', 'E', 'E'] }]

        layer_1 = []
        layer_2 = []
        layer_3 = []
        #test_around_result is formatted in 3 ways.

        for patterns in test_around_result:
            for k, v in patterns[1].iteritems():
                layer_1.append(v)
                # layer_1 is just patterns: ['E', 'E', None]
                layer_2.append([k, v])
                # layer_2 is patterns and associated direction: ['horizontal', ['E', 'E', None]]
                layer_3.append([patterns[0], [k, v]])
                #layer_3 is a 36 item list for each direction for each coordinate: [[1, 1], ['horizontal', ['E', 'E', 'E']]]
        
        # for now I only return layer_3.  See description for filterp() to learn what it does
        return self.filterp(layer_3)


    def choose(self, position_pattern, index):
        '''
        Returns a new matrix index for a given position pattern and index.  For example, if you feed in a position_pattern
        of [[1, 1], ['horizontal', ['E', 'E', 'E']]] and an index of 2...it will return the matrix index of [1, 2] (the grid location
        to the right of the grid location specified by the position pattern.

        Key:
            'horizontal', [left, center, right]
            'vertical', [above, center, below]
            'RLdiagonal', [Upper-right, center, lower-left]
            'LRdiagonal', [Upper-left, center, lower-right]
        '''

        def horizontal(index):
            y = position_pattern[0][0]
            x = position_pattern[0][1]
            
            if index == 0:
                x -= 1
            elif index == 2:
                x += 1

            return [y, x]

    
        def vertical(index):
            y = position_pattern[0][0]
            x = position_pattern[0][1]

            if index == 0:
                y -= 1
            elif index == 2:
                y += 1

            return [y, x]

    
        def RLdiagonal(index):
            y = position_pattern[0][0]
            x = position_pattern[0][1]

            if index == 0:
                y -= 1
                x += 1
            elif index == 2:
                y += 1
                x -= 1

            return [y, x]

    
        def LRdiagonal(index):
            y = position_pattern[0][0]
            x = position_pattern[0][1]

            if index == 0:
                y -= 1
                x -= 1
            elif index == 2:
                y += 1
                x += 1

            return [y, x]


        options = { 'horizontal' : horizontal, 'vertical' : vertical, 'RLdiagonal': RLdiagonal, 'LRdiagonal' : LRdiagonal, }

        if position_pattern[1][0] in options:
            matrix_index = options[position_pattern[1][0]](index)
        else:
            print "%r is not on list of functions" % position_pattern[1][0]
        
        # returns the matrix index [y, x]
        return matrix_index


    def validate(self, pattern_list):
        '''
        Takes pattern_list and removes all pos_patterns which don't have an available 'E' to choose from
        For example, [[1, 1], ['horizontal', ['E', 'E', 'E']]] would remain, but [[2, 0], ['LRdiagonal', ['None', '-', 'None'] would
        be removed
        '''

        v_pattern_list = []
        for pl in pattern_list:
            x = 0
            for i in pl[1][1]:
                if i == 'E':
                    x+=1
            if x>0:
                v_pattern_list.append(pl)

        return v_pattern_list
                    

    def random_move(self, pattern_list):
        '''
        Chooses at random a position_pattern and index from a list of position_patterns
        '''

        position_pattern =random.choice(pattern_list)
        potential_indexes = []
        for i in range(0, len(position_pattern[1][1])):
            if position_pattern[1][1][i] == 'E':
                potential_indexes.append(i)
       
        index = random.choice(potential_indexes)
        return position_pattern, index
            

    def tgp_function(self, grid):
        '''
        This function runs at the beginning of Engine.play_round()
        Creates a pattern list with Player.build_pattern_list() and adds the returned position_patterns to total_game_patterns
        in the database

        The total_game_patterns record is used to compare winning vs non-winning positions.
        '''

        pattern_list = self.filterp(self.build_pattern_list(grid))        
        for p in pattern_list:
            if p not in self.total_game_patterns:    
                self.total_game_patterns.append(p)
        
        
        self.total_game_patterns = self.filterp(self.total_game_patterns)
        tgp_pkl = pickle.dumps(self.total_game_patterns, pickle.HIGHEST_PROTOCOL)

        self.cursor.execute("UPDATE winning_patterns SET total_game_patterns = ?", (tgp_pkl,))
        self.conn.commit()




    def new_pattern_function(self, grid):
        '''
        Compares the current grid's position_patterns against the previous turn's grid's position_patterns.  Appends
        any new position_patterns to the player's new_patterns attribute.  Then it updates previous_layer and returns new_patterns.
        '''
        

        del self.new_patterns[:]
        pattern_list = self.build_pattern_list(grid)

        for pl in pattern_list:
            if pl not in self.previous_layer and pl not in self.new_patterns:
                self.new_patterns.append(pl)

        del self.previous_layer[:]
        self.previous_layer = pattern_list

        return self.new_patterns



    def update_chain(self, position_pattern, index, new_patterns):
        '''
        This function called at the end each round.

        The Chain database keeps track of how often a particular move (position_pattern/index combo) leads to the appearance
        of a new pattern.
        This function is responsible for updating the Chain database.  

        The position_pattern and index chosen in the round
        are used to pull records from the database which keep track of how many times a particular move lead to individual new patterns.

        Any new_patterns which appear 100% of the time get added to the 'top_patterns' column.
        '''

        pos_patt_index_pkl = pickle.dumps([position_pattern, index], pickle.HIGHEST_PROTOCOL)
        
        self.cursor.execute("SELECT * FROM Chain WHERE pos_patt_index = ?", (pos_patt_index_pkl,))
        r = self.cursor.fetchone()

        if r:
            resulting_patterns = pickle.loads(r[1])
            rp_sub_list = []
            for rp in resulting_patterns:
                rp_sub_list.append(rp[0])
                if rp[0] in new_patterns:
                    rp[1] += 1.0
                                        
            for np in new_patterns:
                if np not in rp_sub_list:
                    resulting_patterns.append([np, 1.0])

            times_chosen = r[2] + 1.0
            
            top_patterns = []
            for rp in resulting_patterns:
                if (rp[1]/r[2]) >= 0.99:
                    top_patterns.append(rp[0])
            
            top_patt_str = str(top_patterns)
                               

            res_patt_pkl = pickle.dumps(resulting_patterns, pickle.HIGHEST_PROTOCOL)
            self.cursor.execute('''UPDATE Chain SET resulting_patterns = ?,
                times_chosen = ?, top_patterns = ? WHERE pos_patt_index = ?''', (res_patt_pkl, times_chosen, top_patt_str, pos_patt_index_pkl,))
            self.conn.commit()
            
            
        else:
            final_new_patterns = []
            for np in new_patterns:
                final_new_patterns.append([np, 1.0])
            
            resulting_patterns_pkl = pickle.dumps(final_new_patterns, pickle.HIGHEST_PROTOCOL)
            times_chosen = 1.0
            top_patt_str = ''

            self.cursor.execute("INSERT INTO Chain VALUES (?, ?, ?, ?)", (pos_patt_index_pkl, resulting_patterns_pkl, times_chosen, top_patt_str))
            self.conn.commit()



    def find_leads(self, patterns, grid_list):
        '''
        Receives a list of pattern and pulls from the Chain database, using top_patterns all 
        position_pattern/index combos which always lead to the patterns on the received list appearing.

        Compares these leading position_patterns to the current grid and appends to applicable every pos_patt/index combo which is present.

        Next a series of loops, which are described internally by comments, looks at the list of position_pattern/index combos and
        determines if any refer to the same matrix_index.  If multiple position_pattern/index combos refer to the same matrix_index
        (such as the case when there is a forking opportunity in the game), the position_pattern/index combos which
        point to the most represented matrix index are added to a list.  One of these combos is chosen at random and returned.

        If none of the leading positions is represented on the current grid find_leads() is called once again.  This time, the list
        of patterns sent to find_leads() is the list of leading positions.

        In this way, find_leads() can trace a series of moves backwards until it finds one which is represented on the grid.
        '''
        

        def stringify(lst):
            string = ''
            for l in lst:
                string+=str(l)

            return string

        def destringify(string):
            lst = []
            for s in string:
                lst.append(int(s))
            return lst


        leading_moves = []
        for p in patterns:
            self.cursor.execute("SELECT pos_patt_index FROM Chain WHERE top_patterns LIKE ?", ("%"+str(p)+"%",))
            r = self.cursor.fetchall()

            if r:
                for r in r:
                    leading_moves.append(pickle.loads(r[0]))
            else:
                return False

        next_patt = []
        applicable = []
        for l_m in leading_moves:
            next_patt.append(l_m[0])
            if l_m[0] in grid_list:
                applicable.append(l_m)

        if applicable:
            # Takes each pos_patt_index in applicable and retrieves matrix index with self.choose()
            # Runs the results through a counter and returns a list of the choices which appeared most often            
                   
            matrix_indexes_pre = []
            for ppi in applicable:
                matrix_indexes_pre.append([self.choose(ppi[0], ppi[1]), ppi])
            
            #converts the matrix_indexes into a list of strings for Counter()
            matrix_indexes_stringified = []
            for m_i_p in matrix_indexes_pre:
                matrix_indexes_stringified.append(stringify(m_i_p[0])) 
            
            # Counter returns a dict where each item in the matrix_indexes_stringified list is the key and the number of times
            # it appears is the value
            count = Counter(matrix_indexes_stringified)

            #max_appearance is the max number of times a matrix_index appeared
            max_appearance = max(count.iteritems(), key=itemgetter(1))[1]
            
            # appends each matrix_index that appeared the most times
            most_common_mi_stringified = []
            for k, v in count.iteritems():
                if v == max_appearance:
                    most_common_mi_stringified.append(k)
            
            # Destringifies each of the matrix_indexes
            matrix_indexes = []
            for mcms in most_common_mi_stringified:
                matrix_indexes.append(destringify(mcms))
            
            # appends to final_ppi the position_pattern_indexes, eg. [[[2, 1], ['horizontal', ['+', 'E', '+']]], 1]
            # which, when fed into self.choose(), return one of the matrix_indexes deemed to appear most often in the applicable list
            final_ppi = []
            for m_i_p in matrix_indexes_pre:
                if m_i_p[0] in matrix_indexes:
                    final_ppi.append(m_i_p[1])
                
            
            position_pattern_index = random.choice(final_ppi)
            return position_pattern_index

        else:

            return self.find_leads(next_patt, grid_list) 

            



    def compete(self, grid):
        '''
        Pulls all winning_patterns from winning_patterns database.  Feeds this list into Player.find_leads().
        If find_leads returns a position_pattern/index combo, compete() returns it.  Else, it chooses a position_pattern/index combo
        at random.
        '''
        
        
        self.cursor.execute("SELECT patterns FROM winning_patterns")
        r = self.cursor.fetchone()

        if r:
            winning_patterns = pickle.loads(r[0])
            grid_list = self.build_pattern_list(grid)
            position_pattern_index = self.find_leads(winning_patterns, grid_list)
            
"
            if position_pattern_index:    
                print "Computer move\n"
                return position_pattern_index[0], position_pattern_index[1]
        
            else:
                print "Making random move\n"
                position_pattern, index = self.random_move(self.validate(self.build_pattern_list(grid)))
                
                return position_pattern, index
        else:
            print "No winning patterns found in database"
        


    def find_winning_pos(self):
        '''
        Pulls previous winning_patterns, adds them to list of new_patterns which arose upon game win, removes all patterns which
        have appeared in previous rounds without leading to a win (by comparing to total_game_patterns).  Only patterns which
        lead to a win remain.  Database is updated to contain only these winning_patterns.
        '''

        self.cursor.execute("SELECT patterns, total_game_patterns FROM winning_patterns")
        r = self.cursor.fetchone()
                
        if r:
            winning_patterns = pickle.loads(r[0])

            del self.total_game_patterns[:]
            self.total_game_patterns = pickle.loads(r[1])
            
            for w_p in winning_patterns:
                if w_p not in self.new_patterns:
                    self.new_patterns.append(w_p)

            #This loop is repeated 4 times because some patterns don't register as appearing in total_game_patterns and
            #therefore are not removed.  Repeating the loop seems to take care of this problem.          
            for pattern in self.new_patterns:
                if pattern in self.total_game_patterns:
                    self.new_patterns.remove(pattern)

            for pattern in self.new_patterns:
                if pattern in self.total_game_patterns:
                    self.new_patterns.remove(pattern)

            for pattern in self.new_patterns:
                if pattern in self.total_game_patterns:
                    self.new_patterns.remove(pattern)

            for pattern in self.new_patterns:
                if pattern in self.total_game_patterns:
                    self.new_patterns.remove(pattern)


            winning_patterns_pkl = pickle.dumps(self.new_patterns, pickle.HIGHEST_PROTOCOL)
            self.cursor.execute("UPDATE winning_patterns SET patterns = ?", (winning_patterns_pkl,))
            self.conn.commit()        

        else:
            tgp_pkl = pickle.dumps(self.total_game_patterns, pickle.HIGHEST_PROTOCOL)
            winning_patterns_pkl = pickle.dumps(self.new_patterns, pickle.HIGHEST_PROTOCOL)
            self.cursor.execute("INSERT INTO winning_patterns VALUES (?, ?)", (winning_patterns_pkl, tgp_pkl,))
            self.conn.commit()
     
        
if __name__ == "__main__":        

    player_x = Player("X")
    player_o = Player("O")
    game = Engine(player_x, player_o)
    
    rep = 1
    X = 0
    O = 0
    D = 0

    for r in range(int(repetitions)):
        print rep, "\n"
        result = game.play_game()
        if result == "X":
            X+=1
        elif result == "O":
            O+=1
        elif result == "D":
            D+=1
        player_x.reset_player()
        player_o.reset_player()
        game.reset_board()
        rep+=1

        
    print X, "\n"
    print O, "\n"
    print D



