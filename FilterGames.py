import re

TESTING = False

if TESTING:
    input_file_name = 'first_100_games.txt'
    output_file_name = 'games_with_evals_from_first_100_games.txt'
else:
    input_file_name = 'lichess_db_standard_rated_2025-12.pgn'
    output_file_name = 'games_with_evals.txt'

input_file_directory = '/Users/andrewford/Documents/DataSets/Lichess-Data/'
input_file_path = input_file_directory + input_file_name
input_file = open(input_file_path, 'r')

output_file_directory = '/Users/andrewford/Documents/DataSets/Lichess-Data/FilteredGames/'
output_file_path = output_file_directory + output_file_name
output_file = open(output_file_path, 'w')

WRITE_CONSOLE_OUTPUT = False

WRITE_OUTPUT_FILE = True

COLUMN_NAMES = ['white_elo', 'white_move', 'white_eval', 'white_time_left', 'black_elo', 'black_move', 'black_eval', 'black_time_left', 'result_code'] # column names for output file

# game parameters - ideally make a class or struct for this later
event = '' # rated vs unrated, rapid vs blitz vs classical, etc
url = '' # not needed
date = '' # not needed
match_round = '' # probably not needed
white_username = '' # not needed
black_username = '' # not needed
result = '' # 1-0, 0-1, 1/2-1/2 for white win, black win, draw respectively
utc_date = '' # not needed
utc_time = '' # not needed
white_elo = 0
black_elo = 0
white_rating_diff = 0 # probably not needed, could represent confidence in rating
black_rating_diff = 0 # probably not needed, could represent confidence in rating
eco = '' # opening code, probably not needed
opening = '' # opening name, probably not needed
time_control = '' # will be useful
termination = '' # useful to see if timeout
moves = [] # list of moves in SAN notation with timestamps and evals
has_evals = False # whether or not Stockfish evals are present

LINES_PER_GAME = 20
CONDENSE_SUMMARY = True

# resets all game parameters to default values. Not sure if needed
def reset_game_parameters():
    global event, url, date, match_round, white_username, black_username
    global result, utc_date, utc_time, white_elo, black_elo
    global white_rating_diff, black_rating_diff, eco, opening
    global time_control, termination, moves, has_evals

    event = ''
    url = ''
    date = ''
    match_round = ''
    white_username = ''
    black_username = ''
    result = ''
    utc_date = ''
    utc_time = ''
    white_elo = 0
    black_elo = 0
    white_rating_diff = 0
    black_rating_diff = 0
    eco = ''
    opening = ''
    time_control = ''
    termination = ''
    moves = []
    has_evals = False

def parse_game_line(line):
    global event, url, date, match_round, white_username, black_username
    global result, utc_date, utc_time, white_elo, black_elo
    global white_rating_diff, black_rating_diff, eco, opening
    global time_control, termination, moves, has_evals

    # Example parsing logic; actual implementation will depend on line format
    if line.startswith('[Event '):
        event = line.split('"')[1]
    elif line.startswith('[WhiteElo '):
        white_elo = int(line.split('"')[1])
    elif line.startswith('[BlackElo '):
        black_elo = int(line.split('"')[1])
    elif line.startswith('[WhiteRatingDiff '):
        white_rating_diff = int(line.split('"')[1])
    elif line.startswith('[BlackRatingDiff '):
        black_rating_diff = int(line.split('"')[1])
    elif line.startswith('[Result '):
        result = line.split('"')[1]
    elif line.startswith('[TimeControl '):
        time_control = line.split('"')[1]
    elif line.startswith('[Termination '):
        termination = line.split('"')[1]
    elif line.startswith('1. '):  # Assuming moves start with "1. "
        moves = parse_moves(line) # can move this into the if statement?
        #moves = line
        # Further processing to check for evals can be added here
        if 'eval' in line:
            has_evals = True
        else:
            has_evals = False

def parse_moves(moves_line):
    # Placeholder function to parse moves from a line
    # Pattern for white's moves: 1. e4 { [%eval 0.18] [%clk 0:10:00] }
    # \d+\. matches the move number (e.g., "1.")
    # \s* matches any whitespace after the move number
    # ([^\s]+) captures the actual move (e.g., "e4")
    # \s*\{\s\[\%eval\s.*?\]\s\[\%clk\s.*?\]\s\} matches the eval and clock info in curly braces
    # Pattern for white's moves if eval is forced mate: 18. Qd7+ { [%eval #1] [%clk 0:08:11] }
    # Pattern for white's move if checkmate: 19. Qd7# { [%clk 0:08:11] }
    # Put this in the findall function to get all white moves with evals and clock times
    moves_list_white = re.findall(r'\d+\.\s*([^\s]+)\s*\{\s*\[\%eval\s.*?\]\s*\[\%clk\s.*?\]\s*\}', moves_line)
    # Pattern for black's moves: 1... c6 { [%eval 0.31] [%clk 0:10:00] }
    moves_list_black = re.findall(r'\d+\.{3}\s*([^\s]+)\s*\{\s*\[\%eval\s.*?\]\s*\[\%clk\s.*?\]\s*\}', moves_line)
    evals_list = re.findall(r'\[\%eval\s(.*?)\]', moves_line)
    clock_times_list = re.findall(r'\[\%clk\s(.*?)\]', moves_line)
    return moves_list_white, moves_list_black, evals_list, clock_times_list

def write_game_summary():
    global event, white_elo, black_elo, white_rating_diff, black_rating_diff, result, time_control, termination, moves
    # write these to the output file instead of printing
    if CONDENSE_SUMMARY:
        moves_list_white, moves_list_black, evals_list, clock_times_list = moves
        moves_output = list(zip(moves_list_white, evals_list[0:len(evals_list):2], clock_times_list[0:len(clock_times_list):2], moves_list_black, evals_list[1:len(evals_list):2], clock_times_list[1:len(clock_times_list):2]))
        n_rows_moves = len(moves_output)
        result_code = 1 if result == '1-0' else 0 if result == '0-1' else 0.5
        for i in range(n_rows_moves):
            #for j in range(len(moves_output[i])):
                #moves_output[i][j] = str(moves_output[i][j]) # convert all elements to strings for output
            output_file.write(str(white_elo)+'\t'+('\t'.join(moves_output[i][0:3]))+'\t'+str(black_elo)+'\t'+('\t'.join(moves_output[i][3:6]))+'\t'+str(result_code)+'\n') # separate elements with tabs
            #print('\t'+str(result_code)+'\n') # add result code at the end of the moves line
        #print('\n\n') # add extra newlines to separate games
    else:
        output_file.write(f'[Event "{event}"]\n')
        output_file.write(f'[WhiteElo "{white_elo}"]\n')
        output_file.write(f'[BlackElo "{black_elo}"]\n')
        output_file.write(f'[WhiteRatingDiff "{white_rating_diff}"]\n')
        output_file.write(f'[BlackRatingDiff "{black_rating_diff}"]\n')
        output_file.write(f'[Result "{result}"]\n')
        output_file.write(f'[TimeControl "{time_control}"]\n')
        output_file.write(f'[Termination "{termination}"]\n\n')
        moves_list_white, moves_list_black, evals_list, clock_times_list = moves
        moves_output = list(zip(moves_list_white, evals_list[0:len(evals_list):2], clock_times_list[0:len(clock_times_list):2], moves_list_black, evals_list[1:len(evals_list):2], clock_times_list[1:len(clock_times_list):2]))
        n_rows_moves = len(moves_output)
        for i in range(n_rows_moves):
            for j in range(len(moves_output[i])):
                #moves_output[i][j] = str(moves_output[i][j]) # convert all elements to strings for output
                output_file.write(f'{moves_output[i][j]}\t') # separate elements with tabs
            output_file.write('\n') # add a newline after each row
        output_file.write('\n\n') # add extra newlines to separate games

line_counter = 0
game_counter = 0
games_with_evals_counter = 0
if WRITE_OUTPUT_FILE:
    output_file.write(('\t'.join(COLUMN_NAMES))+'\n') # write header row to output file
    #output_file.write('white_elo\twhite_move\twhite_eval\twhite_time_left\tblack_elo\tblack_move\tblack_eval\tblack_time_left\tresult_code\n') # write header row to output file
for line in input_file:
    line_counter += 1
    if line == '' or line.isspace():
        continue  # skip empty lines
    parse_game_line(line)
    if line.startswith('1. '):  # means we just parsed the line of moves for a game
        game_counter += 1
        if has_evals == True:
            games_with_evals_counter += 1
            if WRITE_CONSOLE_OUTPUT:
                print(f'Game {game_counter} has evaluations.')
                print(f'White Elo: {white_elo}, Black Elo: {black_elo}, Result: {result}')
            if WRITE_OUTPUT_FILE:
                write_game_summary()
        reset_game_parameters()
print(f'Total lines read: {line_counter}')
print(f'Total games read: {game_counter}')
print(f'Total games with evaluations: {games_with_evals_counter}')
print(f'Percentage of games with evaluations: {games_with_evals_counter / game_counter * 100:.2f}%')

#print('Parse moves test:')
#test_moves_line = "1. e4 { [%eval 0.18] [%clk 0:10:00] } 1... c6 { [%eval 0.31] [%clk 0:10:00] } 2. Nf3 { [%eval 0.17] [%clk 0:09:58] } 2... d5 { [%eval 0.21] [%clk 0:10:00] } 3. exd5 { [%eval 0.14] [%clk 0:09:57] } 3... cxd5 { [%eval 0.07] [%clk 0:10:00] } 4. d4 { [%eval 0.0] [%clk 0:09:56] } 4... Bg4 { [%eval 0.26] [%clk 0:10:00] } 5. Be2 { [%eval 0.0] [%clk 0:09:55] } 5... e6 { [%eval 0.0] [%clk 0:09:59] } 6. Nc3 { [%eval -0.22] [%clk 0:09:54] } 6... Bb4 { [%eval -0.12] [%clk 0:09:58] } 7. Bf4 { [%eval -0.13] [%clk 0:09:52] } 7... Nc6 { [%eval -0.19] [%clk 0:09:57] } 8. a3 { [%eval -0.63] [%clk 0:09:50] } 8... Ba5 { [%eval -0.16] [%clk 0:09:55] } 9. b4 { [%eval -0.56] [%clk 0:09:48] } 9... Bc7 { [%eval -0.55] [%clk 0:09:54] } 10. Bxc7 { [%eval -0.61] [%clk 0:09:45] } 10... Qxc7 { [%eval -0.61] [%clk 0:09:54] } 11. O-O { [%eval -0.63] [%clk 0:09:44] } 11... Nxb4?? { [%eval 3.1] [%clk 0:09:45] } 12. axb4? { [%eval 0.32] [%clk 0:09:26] } 12... Qxc3 { [%eval 0.38] [%clk 0:09:43] } 13. Bb5+? { [%eval -1.52] [%clk 0:09:25] } 13... Kd8?! { [%eval -0.84] [%clk 0:09:33] } 14. Bd3 { [%eval -0.88] [%clk 0:08:34] } 14... Bxf3 { [%eval -0.43] [%clk 0:08:26] } 15. Qxf3 { [%eval -0.4] [%clk 0:08:32] } 15... Qxd4?? { [%eval 3.26] [%clk 0:08:24] } 16. Qxf7 { [%eval 3.19] [%clk 0:08:29] } 16... Qf6?? { [%eval 8.22] [%clk 0:08:04] } 17. Qxb7 { [%eval 7.74] [%clk 0:08:26] } 17... Rc8? { [%eval #18] [%clk 0:07:59] } 18. Rxa7 { [%eval 10.43] [%clk 0:08:16] } 18... Ne7?! { [%eval #1] [%clk 0:07:57] } 19. Qd7# { [%clk 0:08:11] } 1-0"
#parsed_white_moves, parsed_black_moves, parsed_evals, parsed_clock_times = parse_moves(test_moves_line)
#print('Parsed white moves without evals:')
#print(parsed_white_moves)
#print('Number of white moves parsed:', len(parsed_white_moves))
#print('Parsed black moves without evals:')
#print(parsed_black_moves)
#print('Number of black moves parsed:', len(parsed_black_moves))
#print('Parsed evals from both players\' moves:')
#print(parsed_evals)
#print('Number of evals parsed:', len(parsed_evals))
#print('Parsed clock times from both players\' moves:')
#print(parsed_clock_times)
#print('Number of clock times parsed:', len(parsed_clock_times))
#print('Moves data as single array (transposed):')
#print(list(zip(parsed_white_moves, parsed_evals[0:len(parsed_evals):2], parsed_clock_times[0:len(parsed_clock_times):2], parsed_black_moves, parsed_evals[1:len(parsed_evals):2], parsed_clock_times[1:len(parsed_clock_times):2])))