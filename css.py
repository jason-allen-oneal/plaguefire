# css.py

CSS = """
Screen {
    background: #0a0618;
    color: white;
}

#layout {
    /* Ensure this is a horizontal layout (handled by Horizontal widget in Python code) */
    /* layout: horizontal; */ 
    height: 100%;
}

#dungeon {
    /* UPDATED: Use 1fr to take remaining space */
    width: 1fr; 
    border: solid #444;
    padding: 0; 
    height: 100%;
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

"""