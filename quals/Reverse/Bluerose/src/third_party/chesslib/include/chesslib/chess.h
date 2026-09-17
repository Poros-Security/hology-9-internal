/*
 * Chess game definitions
 * Created by thearst3rd on 10/24/2020
 */

#pragma once

#include "chesslib/boardlist.h"
#include "chesslib/movelist.h"
#include "chesslib/squareset.h"

typedef enum
{
	tsOngoing,
	tsCheckmate,
	tsDrawStalemate,
	tsDrawClaimed50MoveRule,
	tsDraw75MoveRule,
	tsDrawClaimedThreefold,
	tsDrawFivefold,
	tsDrawInsufficient
} terminalState;

typedef struct
{
	moveList *currentLegalMoves;
	terminalState terminal;
	boardList *boardHistory;
	moveList *moveHistory;
	uint8_t repetitions; 	// How many times we have seen the current position
} chess;

// Creates and initializes a chess game. Must be freed. In FromFen: if invalid FEN, then NULL is returned.
chess *chessCreate();
chess *chessCreateFen(const char *fen);

// Initializes the chess game
void chessInitInPlace(chess *c);
// Returns 0 if successful, 1 if invalid FEN (and does not init)
uint8_t chessInitFenInPlace(chess *c, const char *fen);

// Frees a chess game and all components
void chessFree(chess *c);

// Getters for game struct
board *chessGetBoard(chess *c);
moveList *chessGetLegalMoves(chess *c);
terminalState chessGetTerminalState(chess *c);

boardList *chessGetBoardHistory(chess *c);
moveList *chessGetMoveHistory(chess *c);
uint8_t chessGetRepetitions(chess *c);

// Plays the given move. Returns 0 if successful, 1 if unsuccessful (move was illegal)
uint8_t chessPlayMove(chess *c, move m);
// Undoes the last move played or draw claim. Returns 0 if successful, 1 if unsuccessful (no moves left)
uint8_t chessUndo(chess *c);

// THESE FUNCTIONS MIRROR THE FUNCTIONS IN THE board STRUCT FOR CONVENIENCE
piece chessGetPiece(chess *c, sq s);
pieceColor chessGetPlayer(chess *c);
uint8_t chessGetCastleState(chess *c);
sq chessGetEpTarget(chess *c);
unsigned int chessGetHalfMoveClock(chess *c);
unsigned int chessGetMoveNumber(chess *c);

// Returns a string of all moves in the games history in UCI. Must be freed
char *chessGetMoveHistoryUci(chess *c);

uint8_t chessIsInCheck(chess *c);
uint8_t chessIsSquareAttacked(chess *c, sq s);
char *chessGetFen(chess *c); 	// Returns a string containing FEN, MUST be freed


// Handle claiming draws
uint8_t chessCanClaimDraw50(chess *c);
uint8_t chessCanClaimDrawThreefold(chess *c);
void chessClaimDraw50(chess *c);
void chessClaimDrawThreefold(chess *c);

// Internal - updates the currentLegalMoves, repetitions, and terminalState fields. Called (interally) every move
void chessCalculateFields(chess *c);
