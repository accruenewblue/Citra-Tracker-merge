import PySimpleGUI as sg
import json
import pathlib
import pandas as pd
import re
import io

def log_parser(log):
    log.count('\n--')
    lsplit = log.split('\n--')

    if (lsplit[-1].count('Pokemon X') >= 1) | (lsplit[-1].count('Pokemon Y') >= 1):
        game = 'XY'
    # elif (lsplit[-1].count('Pokemon Y') >= 1):
    #     game = 'XY'
    elif (lsplit[-1].count('Pokemon Omega') >= 1) | (lsplit[-1].count('Pokemon Alpha') >= 1):
        game = 'ORAS'
    # elif (lsplit[-1].count('Pokemon Alpha') >= 1):
    #     game = 'ORAS'
    elif (lsplit[-1].count('Pokemon Sun') >= 1) | (lsplit[-1].count('Pokemon Moon') >= 1):
        game = 'SM'
    # elif (lsplit[-1].count('Pokemon Moon') >= 1):
    #     game = 'SM'
    elif (lsplit[-1].count('Pokemon Ultra') >= 1):
        game = 'USUM'
    else:
        game = 'UNK'

    if game != 'UNK':
        print(f'Log from pokemon {game}.')
    else:
        print('Error reading log.')

    if game in ('XY'):
        gen = 6
        evos = lsplit[1] # done
        mons = lsplit[2] # done
        moves = lsplit[7] # done
        tms = lsplit[8] # done
        tmcompat = lsplit[9] # done
        trainer = lsplit[10] # done
        wildmons = lsplit[12] # done
    elif game in ('ORAS'): # not verified yet
        gen = 6
        evos = lsplit[1] # done
        mons = lsplit[2] # done
        moves = lsplit[7] # done
        tms = lsplit[8] # done
        tmcompat = lsplit[9] # done
        trainer = lsplit[12] # done
        wildmons = lsplit[14] # done
        # tutormoves = lsplit[10]
        # tutorcompat = lsplit[11]
    elif game in ('SM', 'USUM'): # not verified yet, will do after gen 6 is done
        gen = 7
        evos = lsplit[1] # done
        mons = lsplit[2] # done
        moves = lsplit[7] # done
        tms = lsplit[8] # done
        tmcompat = lsplit[9] # done
        trainer = lsplit[12] # done
        wildmons = lsplit[15] # done
        ## to be added later:
        # tutormoves = lsplit[10]
        # tutorcompat = lsplit[11]
        # totems = lsplit[14]


    def parser(data, pattern, s):
        groups = [m.groupdict() for line in data.split(sep=s) if (m := re.match(pattern, line))]
        return groups

    # evolutions
    # evos_regex = r'(?P<preevo>\S+)+\s+(?P<postevo>\S+)?'
    # evos_df = pd.DataFrame(parser(evos.replace('->', ''), evos_regex, '\n')[1:])
    evos_df = pd.DataFrame([l for l in evos.split(sep='\n')][1:-1])
    evos_df[['preevo', 'postevo']] = evos_df[0].str.split('->', expand=True)
    evos_df['postevo'] = evos_df['postevo'].str.replace(' and ',';')
    evos_df['postevo'] = evos_df['postevo'].str.replace(', ',';')
    evos_df = evos_df.drop(columns=0)
    evos_df['preevo'] = evos_df['preevo'].str.strip()
    evos_df['postevo'] = evos_df['postevo'].str.strip()

    # mons
    mons_df = pd.read_csv(io.StringIO(mons.replace('Pokemon Base Stats & Types--','')), sep='|')
    mons_df.columns = mons_df.columns.str.strip()
    mons_df[mons_df.select_dtypes('object').columns] = mons_df[mons_df.select_dtypes('object').columns].apply(lambda x: x.str.strip())
    mons_df[['TYPE1', 'TYPE2']] = mons_df['TYPE'].str.split('/', expand=True)

    # tm compatibility
    tmcompat_df = pd.read_csv(io.StringIO(tmcompat.replace('TM Compatibility--','')), sep='|', header=None)
    tmcompat_df[['NUM', 'NAME']] = tmcompat_df[0].str.strip().str.split(' ', n=1, expand=True)
    tmcompat_df = tmcompat_df.map(lambda x: x.strip() if isinstance(x, str) else x)

    # moves
    moves_df = moves.replace('Pokemon Movesets--\n', '').split('\n\n')
    moves_df = pd.DataFrame(moves_df).rename(columns={0:'mon'})
    moves_df = moves_df.apply(lambda x: x['mon'].split('\n'), axis=1)
    moves_df = pd.DataFrame(moves_df.values.tolist()).add_prefix('col_')
    moves_df.drop(columns=moves_df.columns[1:7], inplace=True)
    moves_regex = r"(?P<num>\d+)+\s+(?P<mon>\S+)+\s[->]+\s+(?P<evo>.+)?"
    moves_label = moves_df['col_0'].str.extract(moves_regex)
    moves_df = pd.concat([moves_label, moves_df], axis=1).drop(columns='col_0')
    moves_df.iloc[:, 3:] = moves_df.iloc[:, 3:].where(moves_df.iloc[:, 3:].apply(lambda x: x.str.startswith('Level')))
    moves_df['evo'] = moves_df['evo'].replace('(no evolution)', '')
    moves_df.dropna(axis=1, how='all', inplace=True)

    # tms
    tm_regex = r"(?P<tmnum>\w+)+\s+(?P<move>.*)"
    tms_df = pd.DataFrame(parser(tms, tm_regex, '\n')[1:])
    tms_df['tmnum'] = tms_df['tmnum'].str.replace('TM', '').astype(int)

    # trainers
    trainer_df = pd.DataFrame(trainer.replace('Trainers Pokemon--\n', '').split('\n'))
    trainer_df[['trainer', 'team']] = trainer_df[0].str.split(' - ', expand=True)
    trainer_df = trainer_df.drop(columns=0)
    trainer_df[['trainernum', 'trainername']] = trainer_df['trainer'].str.split(' \\(', expand=True, n=1)
    trainer_df[['trainerorig', 'trainerrename']] = trainer_df['trainername'].str.split('=>', expand=True, n=1)
    trainer_df = trainer_df.drop(columns=['trainer', 'trainerrename', 'trainername'])
    trainer_team = trainer_df['team'].str.split(',', expand=True)
    for (index, colname) in enumerate(trainer_team):
        new_col1 = 'pkmn_' + str(colname + 1)
        new_col2 = 'lvl_' + str(colname + 1)
        trainer_team[[new_col1, new_col2]] = trainer_team[colname].str.split(' Lv', expand=True)
        trainer_team.drop(columns=colname, inplace=True)
    trainer_df = pd.concat([trainer_df, trainer_team], axis=1).drop(columns='team')
    trainer_df = trainer_df.map(lambda x: x.strip() if isinstance(x, str) else x)

    # wilds
    if gen == 6: #may need to be by game rather than by gen but we're starting here
        wilds_df = pd.DataFrame(wildmons.replace('Wild Pokemon--\n', '').split('\n\n')).rename(columns={0:'set'})
        wilds_df = wilds_df['set'].str.split('\n', expand=True)
        wilds_df[['set', 'loc']] = wilds_df[0].str.split('-', expand=True)
        wilds_df = wilds_df.drop(columns=0)
        for (index, colname) in enumerate(wilds_df.iloc[:, 0:12]):
            new_col1 = 'pkmn_' + str(colname)
            new_col2 = 'lvl_' + str(colname)
            wilds_df[colname] = wilds_df[colname].str[0:24].str.strip()
            wilds_df[[new_col1, new_col2]] = wilds_df[colname].str.split(' Lv', expand=True)
            wilds_df = wilds_df.drop(columns=colname)
    elif gen == 7:
        wilds_df = pd.DataFrame(wildmons.replace('Wild Pokemon--\n', '').split('\n\n')).rename(columns={0:'set'})
        wilds_df = wilds_df['set'].str.split('\n', expand=True)
        wilds_df = wilds_df.map(lambda x: None if str(x).__contains__('SOS') else x)
        wilds_df = wilds_df.dropna(axis=1, how='all')
        wilds_df.columns = list(range(0,11)) # renaming the lists now that we've gotten rid of the SOS cols
        wilds_df[['set', 'loc']] = wilds_df[0].str.split(' - ', expand=True)
        wilds_df = wilds_df.map(lambda x: str(x).replace('Lvs', 'Lv'))
        wilds_df = wilds_df.drop(columns=0)
        for (index, colname) in enumerate(wilds_df.iloc[:, 0:10]):
            new_col1 = 'pkmn_' + str(colname)
            new_col2 = 'lvl_' + str(colname)
            wilds_df[colname] = wilds_df[colname].str[0:29].str.strip()
            wilds_df[[new_col1, new_col2]] = wilds_df[colname].str.split(' Lv', expand=True)
            wilds_df = wilds_df.drop(columns=colname)
    wilds_df = wilds_df.map(lambda x: x.strip() if isinstance(x, str) else x)

    # joins for easier event handling later
    pokemon = pd.merge(mons_df, evos_df, how = 'left', left_on='NAME', right_on='preevo').drop(columns='preevo').rename(columns={'postevo':'EVOLUTION'})
    pokemon = pd.merge(pokemon, moves_df, how='left', left_on='NAME', right_on='mon').drop(columns=['num', 'mon', 'evo'])
    pokemon.columns = pokemon.columns.str.replace('col_', 'move_')
    pokemon['EVOLUTION'] = pokemon['EVOLUTION'].fillna('')
    pokemon = pokemon.sort_values('NAME').reset_index().drop(columns='index')
    return pokemon, wilds_df, tms_df, tmcompat_df, gen, game


# charting stats
def statchart(mon, graph):
    base = 50
    i = 0
    stat = ['HP', 'ATK', 'DEF', 'SPA', 'SPD', 'SPE']
    for s in mon[3:9]:
        x1 = 70 + (40 * i)
        y1 = base
        x2 = 100 + (40 * i)
        y2 = base + (s * .5)
        if s >= 180:
            graph.draw_rectangle((x1,y1), (x2,y2), line_color='green', fill_color='green')
        elif s <= 40:
            graph.draw_rectangle((x1,y1), (x2,y2), line_color='red', fill_color='red')
        else:
            graph.draw_rectangle((x1,y1), (x2,y2), line_color='white', fill_color='white')
        graph.DrawText(stat[i], location=((x1 + x2)/2, base-2), color='white', text_location=sg.TEXT_LOCATION_TOP, font=('Franklin Gothic Medium', 12))
        graph.DrawText(s, location=((x1 + x2)/2, y2+2), color='white', text_location=sg.TEXT_LOCATION_BOTTOM, font=('Franklin Gothic Medium', 12))
        i += 1

    graph.DrawText(f'{mon.iloc[1]} ({sum(mon.iloc[3:9])} BST)', location=(70, base+180), color='#f0f080', text_location=sg.TEXT_LOCATION_TOP_LEFT, font=('Franklin Gothic Medium', 16))
    graph.DrawLine(point_from=(65,base), point_to=(305,base), color='white')


def movelist(mon, logmoves = [], mvlist = []):
    mon = mon.to_list()
    i = 0
    logmoves = []
    logmoves.append([sg.Text(f'Moveset:', text_color='#f0f080', font=('Franklin Gothic Medium', 14), visible = True)])
    mvlist = []
    while i < len(mon):
        if str(mon[i]) != 'nan':
            mon[i] = str(mon[i]).replace('Level ', '')
            logmoves.append([sg.Text(mon[i], text_color='white', font=('Franklin Gothic Medium', 12), key = f'-log-ml{i}-', visible = True, pad=(0,0,0,0))])
            mvlist.append(mon[i])
        else:
            logmoves.append([sg.Text('', text_color='white', font=('Franklin Gothic Medium', 12), key = f'-log-ml{i}-', pad=(0,0,0,0))])
        i += 1
    return logmoves, mvlist


def abillist(mon):
    alist = mon[['ABILITY1', 'ABILITY2', 'ABILITY3']]
    logabils = []
    logabils.append([sg.Text(f'Abilities:', text_color='#f0f080', font=('Franklin Gothic Medium', 14), visible = True)])
    i = 0
    while i < len(alist):
        if i == 2:
            logabils.append([sg.Text(f'{alist.iloc[i]} (HA)', text_color='white', font=('Franklin Gothic Medium', 12), key = f'-log-al{i}-', visible = True)])
        else:
            logabils.append([sg.Text(alist.iloc[i], text_color='white', font=('Franklin Gothic Medium', 12), key = f'-log-al{i}-', visible = True)])
        i += 1
    return logabils, alist


def evolist(mon):
    logevos = []
    elist = mon['EVOLUTION']
    logevos.append([sg.Text(f'Evolutions:', text_color='#f0f080', font=('Franklin Gothic Medium', 14), visible = True)])
    if elist == '':
        logevos.append([sg.Text(f'None', text_color='white', font=('Franklin Gothic Medium', 12), key = f'-log-evos-', visible = True)])
        elist = 'None'
    elif elist.count(';') in (1, 2):
        elist = elist.replace(';', '\n')
        logevos.append([sg.Text(f'{elist}', text_color='white', font=('Franklin Gothic Medium', 12), key = f'-log-evos-', visible = True)])
    elif elist.count(';') > 2:
        i = 0
        x = elist.count(';')
        while i < x:
            elist = elist.replace(';', ', ', 1)
            elist = elist.replace(';', ',\n', 1)
            i += 2
        logevos.append([sg.Text(f'{elist}', text_color='white', font=('Franklin Gothic Medium', 10), key = f'-log-evos-', visible = True)])
    else:
        logevos.append([sg.Text(f'{elist}', text_color='white', font=('Franklin Gothic Medium', 12), key = f'-log-evos-', visible = True)])
    return logevos, elist

def tmlist(mon, game, tmcompat_df, tms_df):
    logtms1, logtms4, logtmsfull, tmtext, tmtextfull = [], [], [], [], []
    tmdict, tmdictfull = {}, {}
    if game == 'XY':
        gymtmlist = [83, 39, 98, 86, 24, 99, 4, 13]
    elif game == 'ORAS':
        gymtmlist = [39, 8, 72, 50, 67, 19, 4, 31] #TM31 is 
    elif game == 'SM':
        gymtmlist = [4, 13, 24, 39, 83, 86, 98, 99]
    elif game == 'USUM':
        gymtmlist = [1, 19, 54, 43, 67, 29, 66]
    logtms1.append([sg.Text(f'Leader TMs:', text_color='#f0f080', font=('Franklin Gothic Medium', 14), visible = True)])
    i,j = 0,0
    while i < len(gymtmlist):
        if tmcompat_df.iloc[mon.iloc[0]-1, gymtmlist[i]] == '-':
            logtms1.append([sg.Text(f'TM{tms_df['tmnum'][gymtmlist[i]-1]} {tms_df['move'][gymtmlist[i]-1]}', text_color='white', font=('Franklin Gothic Medium', 10), key = f'-log-gymtm1{i}-', visible = True)])
            logtms4.append([sg.Text(f'TM{tms_df['tmnum'][gymtmlist[i]-1]} {tms_df['move'][gymtmlist[i]-1]}', text_color='white', font=('Franklin Gothic Medium', 10), key = f'-log-gymtm4{i}-', visible = True)])
            tmdict[f'TM{tms_df['tmnum'][gymtmlist[i]-1]} {tms_df['move'][gymtmlist[i]-1]}'] = False
        else:
            logtms1.append([sg.Text(f'TM{tms_df['tmnum'][gymtmlist[i]-1]} {tms_df['move'][gymtmlist[i]-1]}', text_color='#339ec4', font=('Franklin Gothic Medium', 10), key = f'-log-gymtm1{i}-', visible = True)])
            logtms4.append([sg.Text(f'TM{tms_df['tmnum'][gymtmlist[i]-1]} {tms_df['move'][gymtmlist[i]-1]}', text_color='#339ec4', font=('Franklin Gothic Medium', 10), key = f'-log-gymtm4{i}-', visible = True)])
            tmdict[f'TM{tms_df['tmnum'][gymtmlist[i]-1]} {tms_df['move'][gymtmlist[i]-1]}'] = True
        tmtext.append(f'TM{tms_df['tmnum'][gymtmlist[i]-1]} {tms_df['move'][gymtmlist[i]-1]}')
        i += 1
    while j < 100: # 100 TMs in both gens 6 and 7, there are HMs in the list so need to use flat number
        if tmcompat_df.iloc[mon.iloc[0]-1, j + 1] == '-':
            logtmsfull.append([sg.Text(f'TM{tms_df['tmnum'][j]} {tms_df['move'][j]}', text_color='white', font=('Franklin Gothic Medium', 10), key = f'-log-fulltm{j}-', visible = True)])
            tmdictfull[f'TM{tms_df['tmnum'][j]} {tms_df['move'][j]}'] = False
        else:
            logtmsfull.append([sg.Text(f'TM{tms_df['tmnum'][j]} {tms_df['move'][j]}', text_color='#339ec4', font=('Franklin Gothic Medium', 10), key = f'-log-fulltm{j}-', visible = True)])
            tmdictfull[f'TM{tms_df['tmnum'][j]} {tms_df['move'][j]}'] = True
        tmtextfull.append(f'TM{tms_df['tmnum'][j]} {tms_df['move'][j]}')
        j += 1
    return logtms1, logtms4, logtmsfull, gymtmlist, tmdict, tmdictfull, tmtext, tmtextfull

def pivotlist(game, gen, wilds_df):
    logpivotlocs, logpivotbase1, logpivotbase2 = [], [], []
    pivottext = {}
    if game == 'XY':
        sets = ['Set #22', 'Set #138', 'Set #23', 'Set #132']
        locs = ['Route 2', 'Santalune Forest', 'Route 3', 'Route 22']   
    elif game == 'ORAS':
        sets = ['Set #34', 'Set #39', 'Set #48', 'Set #57', 'Set #346']
        locs = ['Route 101', 'Route 102', 'Route 103', 'Route 104', 'Petalburg Woods']
    elif gen == 7:
        sets = ['Set #1', 'Set #2', 'Set #12', 'Set #13', 'Set #14', 'Set #3', 'Set #10', 'Set #80', 'Set #81', 'Set #82', 'Set #83', 'Set #29', 'Set #31', 'Set #28', 'Set #30', 'Set #49', 'Set #53', 'Set #52', 'Set #54', 'Set #56', 'Set #57', 'Set #68', 'Set #69', 'Set #34', 'Set #43', 'Set #47', 'Set #70', 'Set #71']
        locs = ['Route 1 Grass #1', 'Route 1 Grass #2', 'Route 1 Grass #3', 'Route 1 Grass #4', 'Route 1 Grass #5', "Professor's House #1", "Professor's House #2", 'Trainers School #1', 'Trainers School #2', 'Trainers School #3', 'Trainers School #4', 'Hauoli Grass Area #1', 'Hauoli Grass Area #2', 'Hauoli Grass Area #3', 'Hauoli Grass Area #4', 'Route 2 Grass #1', 'Route 2 Grass #2', 'Route 2 Grass #3', 'Route 2 Grass #4', 'Route 2 Grass #5', 'Route 2 Grass #6', 'Hauoli Cemetary #1', 'Hauoli Cemetary #2', 'Route 3 Grass #1', 'Route 3 Grass #2', 'Route 3 Grass #3', 'Melemele Meadow', 'Seaward Cave']
    pivotlocs = pd.merge(wilds_df, pd.DataFrame(sets, locs).reset_index(), how = 'inner', left_on='set', right_on=0).rename(columns={'index':'locname'})

    f1 = ('Franklin Gothic Medium', 12)
    f2 = ('Franklin Gothic Medium', 10)
    logpivotlocs.append([sg.Text(f'Locations:', text_color='#f0f080', font=f1, visible = True)])
    logpivotbase1.append([sg.Text(f'Pokemon', text_color='#f0f080', font=f1, visible = True)])
    logpivotbase2.append([sg.Text(f'Level', text_color='#f0f080', font=f1, visible = True)])

    for i in range(0, len(pivotlocs)):
        logpivotlocs.append([sg.Text(f'{pivotlocs['locname'][i]}', text_color='white', font=f2, key = f'-logpivot-loc{i}-', visible = True, enable_events=True)])
        j = 1
        if gen == 6:
            while j <= 12: # 12 encounter slots in gen 6
                if i == 0:
                    logpivotbase1.append([sg.Text('', text_color='white', font=f2, key = f'-logpivot-mon{j}-', visible = True, justification='c')])
                    logpivotbase2.append([sg.Text('', text_color='white', font=f2, key = f'-logpivot-lvl{j}-', visible = True, justification='c')])
                pivottext[f'{i}-{j}'] = [f'{pivotlocs[f'pkmn_{j}'][i]}', f'{pivotlocs[f'lvl_{j}'][i]}']
                j += 1
        elif gen == 7: 
            while j <= 10: # 10 encounter slots in gen 7
                if i == 0:
                    logpivotbase1.append([sg.Text('', text_color='white', font=f2, key = f'-logpivot-mon{j}-', visible = True, justification='c')])
                    logpivotbase2.append([sg.Text('', text_color='white', font=f2, key = f'-logpivot-lvl{j}-', visible = True, justification='c')])
                pivottext[f'{i}-{j}'] = [f'{pivotlocs[f'pkmn_{j}'][i]}', f'{pivotlocs[f'lvl_{j}'][i]}']
                j += 1
    return logpivotlocs, logpivotbase1, logpivotbase2, pivottext

def trainerlist(game):
    if game == 'XY':
        name = ['Viola', 'Grant', 'Korrina', 'Ramos', 'Clemont', 'Valarie', 'Olympia', 'Wulfric']
        idx = [5, 75, 20, 21, 22, 23, 24, 25]
    elif game == 'ORAS':
        name = ['Viola', 'Grant', 'Korrina', 'Ramos', 'Clemont', 'Valarie', 'Olympia', 'Wulfric']
        idx = [6, 76, 21, 22, 23, 24, 25, 26]
    elif game in ('SM', 'USUM'):
        name = ['Viola', 'Grant', 'Korrina', 'Ramos', 'Clemont', 'Valarie', 'Olympia', 'Wulfric']
        idx = [6, 76, 21, 22, 23, 24, 25, 26]
    return name, idx

def searchfcn(pokemon, p):
    pkmnnum = pokemon.loc[pokemon['NUM'] == (p + 1)].iloc[0,0]
    l = pokemon['NAME'].to_list()
    l.sort() # this one's what we use for the actual input box
    lcase = pokemon['NAME'].str.casefold().to_list() # allows case insensitivity
    searchpopup = [
        [sg.Text('Pokemon search')],
        [sg.InputCombo(l, enable_events=True, key='-log-pkmnsearch-')],
        [sg.Button('Search', key='-search-'), sg.Button('Cancel')]
    ] 
    window = sg.Window('Pokemon Search', searchpopup).Finalize()
    
    while True:
        event, values = window.read()

        if (event == sg.WINDOW_CLOSED) or (event == 'Cancel'):
            try:
                pkmnnum = pokemon.loc[pokemon['NUM'] == p].iloc[0,0]
            except:
                pkmnnum = 0
            break
        elif event == '-search-':
            try:
                pkmnnum = lcase.index(values['-log-pkmnsearch-'].casefold())
            except:
                sg.popup_ok('Pokemon not found.', title='Error')
                pkmnnum = pokemon.loc[pokemon['NUM'] == p].iloc[0,0]
            break

    window.close()

    return pkmnnum

def logviewer_layout(pokemonnum, pokemon, gen, logtms1, logabils, logmoves, logevos, logpivotbase1, logpivotbase2, graph, logpivotlocs, logtms4, logtmsfull):
    bwidth = 1
    bpad = (1,1,0,0)
    navbar = {}
    if gen == 6:
        bfont = ('Franklin Gothic Medium', 12)
        for i in range(1, 7):
            navbar[i]=[[
                sg.Text(' Pokemon ', enable_events=True, key=f'-lognav-pkmn{i}-', relief='groove', border_width=bwidth, pad=bpad, font=bfont, justification='c'),
                sg.Text(' Trainers ', enable_events=True, key=f'-lognav-trainer{i}-', relief='groove', border_width=bwidth, pad=bpad, font=bfont, justification='c'),
                sg.Text(' Pivots ', enable_events=True, key=f'-lognav-pivot{i}-', relief='groove', border_width=bwidth, pad=bpad, font=bfont, justification='c'),
                sg.Text(' TMs ', enable_events=True, key=f'-lognav-tm{i}-', relief='groove', border_width=bwidth, pad=bpad, font=bfont, justification='c'),
                # sg.Text(' Info ', enable_events=True, key=f'-lognav-info{i}-', relief='groove', border_width=1, pad=bpad, font=bfont),
                sg.Text(' Search ', enable_events=True, key=f'-lognav-search{i}-', relief='groove', border_width=1, pad=bpad, font=bfont, justification='c'),
                sg.Text(' X ', enable_events=True, key=f'-lognav-exit{i}-', relief='groove', border_width=1, pad=bpad, font=bfont, justification='c'),
            ]]
    elif gen == 7: # not complete, will need to fill in later
        bfont = ('Franklin Gothic Medium', 10) # need smaller font because more nav bar things, may choose to go to two rows instead but we'll see if thats needed (hopefully not), could also use abbreviations; might also roll tutor into TM for gen 7
        for i in range(1, 8):
            navbar[i]=[[
                sg.Text(' Pokemon ', enable_events=True, key=f'-lognav-pkmn{i}-', relief='groove', border_width=bwidth, pad=bpad, font=bfont),
                sg.Text(' Trainers ', enable_events=True, key=f'-lognav-trainer{i}-', relief='groove', border_width=bwidth, pad=bpad, font=bfont),
                sg.Text(' Pivots ', enable_events=True, key=f'-lognav-pivot{i}-', relief='groove', border_width=bwidth, pad=bpad, font=bfont),
                sg.Text(' TMs ', enable_events=True, key=f'-lognav-tm{i}-', relief='groove', border_width=bwidth, pad=bpad, font=bfont),
                # sg.Text(' Tutors ', enable_events=True, key=f'-lognav-tutor{i}-', relief='groove', border_width=1, pad=bpad, font=bfont),
                # sg.Text(' Info ', enable_events=True, key=f'-lognav-info{i}-', relief='groove', border_width=1, pad=bpad, font=bfont),
                sg.Text(' Search ', enable_events=True, key=f'-lognav-search{i}-', relief='groove', border_width=1, pad=bpad, font=bfont),
            ]]


    brcol1 = [[
        sg.Column([
            [sg.Column(logtms1, size=(150,220)),],
            [sg.Column(logabils, size=(170,120))],
        ])
    ]]
    blcol1 = [[
        sg.Column([
            [sg.Column(logmoves, scrollable=True, vertical_scroll_only=True, size=(150,220)),],
            [sg.Column(logevos, size=(170,120))],
        ])
    ]]

    bccol3 = [logpivotbase1]
    brcol3 = [logpivotbase2]

    layout_pkmn = [
        [sg.Column(navbar[1], key='-log-navbar1-', size=(340,35), justification='c')],
        [graph], 
        [
            sg.Column(blcol1, key='-log-blcol-', size=(170,350), pad=(5,0,0,0)),
            sg.Column(brcol1, key='-log-brcol-', size=(170,350), pad=(5,0,0,0))
        ],
    ]

    layout_trainers = [
        [sg.Column(navbar[2], key='-log-navbar2-', size=(340,35), justification='c')],
        [sg.Text('Coming soon!')],
    ]

    layout_pivots = [
        [sg.Column(navbar[3], key='-log-navbar3-', size=(340,35), justification='c')],
        [
            sg.Column(logpivotlocs, key='-log-pivotlocs-', size=(150,350), justification='l'),
            sg.Column(logpivotbase1, size=(100,350)), 
            sg.Column(logpivotbase2, size=(50,350)),
        ], 
    ]

    layout_tms = [
        [sg.Column(navbar[4], key='-log-navbar4-', size=(340,35), justification='c')],
        [sg.Text(f'{pokemon.iloc[pokemonnum,1]} ({sum(pokemon.iloc[pokemonnum,3:9])} BST)', font=('Franklin Gothic Medium', 16), text_color='#f0f080', key='-log-tmpkmn-')],
        [
            sg.Text(f'Gym TMs:', font=('Franklin Gothic Medium', 14), text_color='#f0f080', size=15),
            sg.Text(f'All TMs:', font=('Franklin Gothic Medium', 14), text_color='#f0f080'),
        ],
        [sg.Column([
            [
                sg.Column(logtms4, size=(150,400)),
                sg.Column(logtmsfull, size=(150,400), scrollable=True, vertical_scroll_only=True),
            ],
        ])]
    ]
    # layout_tutors = [
    #     [sg.Column(navbar[5], key='-log-navbar4-', size=(340,35), justification='c')],
    # ]
    # layout_info = [
    #     [sg.Column(navbar[6], key='-log-navbar4-', size=(340,35), justification='c')],
    # ]
    # layout_search = [
    #     [sg.Column(navbar[7], key='-log-navbar4-', size=(340,35), justification='c')],
    # ]

    layout_logview = [[
        sg.Column(layout_pkmn, key='-log-layout1-', visible=True), 
        sg.Column(layout_trainers, key='-log-layout2-', visible=False), 
        sg.Column(layout_pivots, key='-log-layout3-', visible=False), 
        sg.Column(layout_tms, key='-log-layout4-', visible=False), 
    ]]
    return layout_logview