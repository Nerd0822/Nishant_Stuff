import pygame as p  # Import the Pygame library for graphics and event handling


class GameState:
    """
    This class manages the state of the chess game, including the board, moves, and whose turn it is.
    """
    def __init__(self):
        # Board is an 8x8 2D list, each element represents a square.
        self.board = [
            ["bR", "bN", "bB", "bQ", "bk", "bB", "bN", "bR"],
            ["bP", "bP", "bP", "bP", "bP", "bP", "bP", "bP"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wP", "wP", "wP", "wP", "wP", "wP", "wP", "wP"],
            ["wR", "wN", "wB", "wQ", "wk", "wB", "wN", "wR"]
        ]
        self.white_to_move = True  # White starts the game
        self.move_log = []  # Log of all moves made

    def make_move(self, move):
        """
        Updates the board with the move and logs it.
        """
        self.board[move.start_row][move.start_col] = "--"
        self.board[move.end_row][move.end_col] = move.piece_moved
        self.move_log.append(move)  # Log the move
        self.white_to_move = not self.white_to_move  # Switch turn


class Move:
    """
    Represents a move in the game. Holds the starting and ending position of the move, as well as the moved piece and any captured piece.
    """
    rank_to_rows = {"1": 7, "2": 6, "3": 5, "4": 4, "5": 3, "6": 2, "7": 1, "8": 0}
    rows_to_ranks = {v: k for k, v in rank_to_rows.items()}

    files_to_cols = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
    cols_to_files = {v: k for k, v in files_to_cols.items()}

    def __init__(self, start_sq, end_sq, board):
        self.start_row = start_sq[0]
        self.start_col = start_sq[1]
        self.end_row = end_sq[0]
        self.end_col = end_sq[1]
        self.piece_moved = board[self.start_row][self.start_col]
        self.piece_captured = board[self.end_row][self.end_col]

    def get_chess_notation(self):
        """
        Returns the move in chess notation (e.g., e2e4).
        """
        return self.get_rank_file(self.start_row, self.start_col) + self.get_rank_file(self.end_row, self.end_col)

    def get_rank_file(self, r, c):
        """
        Converts the row and column into chess notation (e.g., e4).
        """
        return self.cols_to_files[c] + self.rows_to_ranks[r]


# Constants for the board dimensions, square size, and game settings
WIDTH = HEIGHT = 512
DIMENSION = 8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 30
IMAGES = {}

def load_images():
    """
    Load images of chess pieces into the IMAGES dictionary.
    Removed the os module; now using direct relative paths.
    """
    pieces = ["wR", "wN", "wB", "wQ", "wk", "wP", "bQ", "bk", "bB", "bN", "bR", "bP"]
    for piece in pieces:
        try:
            image_path = f"nishant_stuff/chess_project/images/{piece}.png"  # Hard-coded path
            IMAGES[piece] = p.transform.scale(
                p.image.load(image_path), (SQ_SIZE, SQ_SIZE)
            )
        except FileNotFoundError:
            print(f"Error: Image file for {piece} not found at {image_path}")

def main():
    """
    Main driver function for the chess program.
    """
    p.init()  # Initialize Pygame
    screen = p.display.set_mode((WIDTH, HEIGHT))  # Set up the display window
    clock = p.time.Clock()
    screen.fill(p.Color("white"))  # Fill the screen with white background
    gs = GameState()  # Create a new game state
    load_images()  # Load images of chess pieces

    run = True
    sq_selected = ()  # The currently selected square (if any)
    player_clicks = []  # The squares the player has clicked
    valid_moves = []  # Placeholder for valid moves generation
    game_over = False  # Boolean flag to track if the game is over

    while run:
        for e in p.event.get():
            if e.type == p.QUIT:
                run = False  # Quit the game if the user closes the window
            elif e.type == p.MOUSEBUTTONDOWN and not game_over:
                location = p.mouse.get_pos()  # Get mouse position
                col = location[0] // SQ_SIZE  # Column of the square
                row = location[1] // SQ_SIZE  # Row of the square
                
                if sq_selected == (row, col):  # Deselect if clicked again on the same square
                    sq_selected = ()
                    player_clicks = []
                else:
                    sq_selected = (row, col)  # Select the new square
                    player_clicks.append(sq_selected)

                if len(player_clicks) == 2:  # If two squares are selected
                    move = Move(player_clicks[0], player_clicks[1], gs.board)
                    if move.piece_moved != "--":  # Only make the move if the piece is not empty
                        print(move.get_chess_notation())
                        gs.make_move(move)  # Update the game state with the move
                        sq_selected = ()  # Reset selection
                        player_clicks = []  # Reset player clicks

                        # Check for checkmate (simplified logic placeholder)
                        if checkmate_detected(gs):
                            print("Checkmate!")
                            game_over = True

            elif e.type == p.KEYDOWN:
                if e.key == p.K_u:  # Undo move if 'u' key is pressed
                    if gs.move_log:
                        undo_move(gs)

        draw_game_state(screen, gs)  # Redraw the game state
        clock.tick(MAX_FPS)  # Maintain the desired FPS
        p.display.flip()  # Update the display


def undo_move(gs):
    """
    Revert the last move from the move log.
    """
    if len(gs.move_log) > 0:
        last_move = gs.move_log.pop()  # Get the last move
        # Undo the move on the board
        gs.board[last_move.start_row][last_move.start_col] = last_move.piece_moved
        gs.board[last_move.end_row][last_move.end_col] = last_move.piece_captured
        gs.white_to_move = not gs.white_to_move  # Switch turns


def checkmate_detected(gs):
    """
    Check if the current player is in checkmate.
    Placeholder: Needs valid move generation and king safety checks.
    """
    return False  # Replace with real checkmate detection logic


def draw_game_state(screen, gs):
    """
    Draw the game state, including the board and pieces.
    """
    draw_board(screen)  # Draw the chessboard
    draw_pieces(screen, gs.board)  # Draw the pieces on the board


def draw_board(screen):
    """
    Draw the chessboard with alternating colors.
    """
    colors = [p.Color("white"), p.Color("lightblue")]
    for row in range(DIMENSION):
        for col in range(DIMENSION):
            color = colors[(row + col) % 2]  # Alternate colors
            p.draw.rect(screen, color, p.Rect(col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE))


def draw_pieces(screen, board):
    """
    Draw the chess pieces on the board.
    """
    for row in range(DIMENSION):
        for col in range(DIMENSION):
            piece = board[row][col]
            if piece != "--":
                screen.blit(IMAGES[piece], p.Rect(col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE))  # Draw the piece


if __name__ == "__main__":
    main()  # Run the main game loop
