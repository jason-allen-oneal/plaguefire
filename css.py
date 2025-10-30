# css.py

CSS = """
#game-root {
    height: 100%;
    width: 100%;
}

#layout {
    height: 100%;
}

#main-column {
    width: 1fr;
    height: 100%;
}

#dungeon {
    width: 1fr; 
    border: solid #444;
    padding: 0; 
    height: 1fr;
}

#hud {
    width: 30; /* Content width is 30 */
    border: solid white;
    padding: 1; /* Padding adds 1 left + 1 right */
    background: #120a24;
    height: 100%;
    /* Total width becomes 32 due to padding */
    box-sizing: border-box; 
}

#hotkey-container {
    height: 14;
    max-height: 18;
    border: solid #444;
    border-top: none;
    background: #080512;
    padding: 0 1;
}

#scores-root {
    align-horizontal: center;
    align-vertical: top;
    padding: 2 4;
}

#scores-board {
    border: solid #444;
    padding: 1 2;
    background: #05030c;
    text-align: center;
}

#scores-details {
    padding: 0 2;
    width: 80;
    text-align: left;
}

#death-tombstone {
    padding: 2;
    text-align: center;
}

#creation_layout {
    height: 100%;
    width: 100%;
    content-align: center middle;
}

#creation_text {
    content-align: center middle; 
}

/* Styles for continue_screen (Optional) */
#continue_title {
    text-align: center;
    padding: 1 0;
}
#save_list {
    padding: 1 2;
}

/* Styles for shop_screen (Optional) */
#shop-display {
    padding: 1;
}

/* Styles for spell screens */
#spell-list, #spell-options-list {
    padding: 1 2;
    height: auto;
}

.spell-option-text {
    padding: 0 1;
}

.centered-message {
    text-align: center;
    padding: 2;
}

/* Styles for target selector */
#target-list {
    padding: 1 2;
    height: auto;
}

.target-option-text {
    padding: 0 1;
}

"""
