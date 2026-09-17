/*
 * Chess game implementation
 * Created by thearst3rd on 10/24/2020
 */

#include <stdlib.h>

#include "chesslib/chess.h"
#include "chesslib/move.h"

chess *chessCreate()
{
	return chessCreateFen(INITIAL_FEN);
}

chess *chessCreateFen(const char *fen)
{
	chess *c = (chess *) malloc(sizeof(chess));

	if (chessInitFenInPlace(c, fen))
	{
		free(c);
		return NULL;
	}

	return c;
}

void chessInitInPlace(chess *c)
{
	chessInitFenInPlace(c, INITIAL_FEN);
}

uint8_t chessInitFenInPlace(chess *c, const char *fen)
{
	board *b = boardCreateFromFen(fen);
	if (b == NULL)
		return 1;

	c->boardHistory = boardListCreate();
	boardListAdd(c->boardHistory, b);

	c->moveHistory = moveListCreate();

	c->currentLegalMoves = NULL;
	c->repetitions = 1;
	c->terminal = tsOngoing;

	// Calculates repetitions and terminal state
	chessCalculateFields(c);

	return 0;
}

void chessFree(chess *c)
{
	boardListFree(c->boardHistory);
	moveListFree(c->moveHistory);
	moveListFree(c->currentLegalMoves);
	free(c);
}

board *chessGetBoard(chess *c)
{
	return c->boardHistory->tail->board;
}

moveList *chessGetLegalMoves(chess *c)
{
	return c->currentLegalMoves;
}

terminalState chessGetTerminalState(chess *c)
{
	return c->terminal;
}

boardList *chessGetBoardHistory(chess *c)
{
	return c->boardHistory;
}

moveList *chessGetMoveHistory(chess *c)
{
	return c->moveHistory;
}

uint8_t chessGetRepetitions(chess *c)
{
	return c->repetitions;
}

uint8_t chessPlayMove(chess *c, move m)
{
	if (c->terminal != tsOngoing)
		return 1;

	uint8_t found = 0;

	for (moveListNode *n = c->currentLegalMoves->head; n; n = n->next)
	{
		if (moveEq(m, n->move))
		{
			found = 1;
			break;
		}
	}

	if (!found)
		return 1;

	board *newBoard = boardPlayMove(chessGetBoard(c), m);

	boardListAdd(c->boardHistory, newBoard);
	moveListAdd(c->moveHistory, m);

	chessCalculateFields(c);

	return 0;
}

uint8_t chessUndo(chess *c)
{
	// If there's only one board (so, no moves), return failure
	if (c->boardHistory->head == c->boardHistory->tail)
		return 1;

	if (c->terminal == tsDrawClaimedThreefold || c->terminal == tsDrawClaimed50MoveRule)
	{
		c->terminal = tsOngoing;
	}
	else
	{
		boardListUndo(c->boardHistory);
		moveListUndo(c->moveHistory);
	}

	chessCalculateFields(c);

	return 0;
}

// Functions that mirror the board struct
piece chessGetPiece(chess *c, sq s)
{
	return boardGetPiece(chessGetBoard(c), s);
}

pieceColor chessGetPlayer(chess *c)
{
	return chessGetBoard(c)->currentPlayer;
}

uint8_t chessGetCastleState(chess *c)
{
	return chessGetBoard(c)->castleState;
}

sq chessGetEpTarget(chess *c)
{
	return chessGetBoard(c)->epTarget;
}

unsigned int chessGetHalfMoveClock(chess *c)
{
	return chessGetBoard(c)->halfMoveClock;
}

unsigned int chessGetMoveNumber(chess *c)
{
	return chessGetBoard(c)->moveNumber;
}

char *chessGetMoveHistoryUci(chess *c)
{
	return moveListGetUciString(chessGetMoveHistory(c));
}

uint8_t chessIsInCheck(chess *c)
{
	return boardIsInCheck(chessGetBoard(c));
}

// TODO, refactor to use sqSet attacked instead
uint8_t chessIsSquareAttacked(chess *c, sq s)
{
	board *b = chessGetBoard(c);
	return boardIsSquareAttacked(b, s, b->currentPlayer == pcWhite ? pcBlack : pcWhite);
}

char *chessGetFen(chess *c)
{
	return boardGetFen(chessGetBoard(c));
}

uint8_t chessCanClaimDraw50(chess *c)
{
	return (c->terminal == tsOngoing) && (chessGetBoard(c)->halfMoveClock >= 100);
}

uint8_t chessCanClaimDrawThreefold(chess *c)
{
	return (c->terminal == tsOngoing) && (c->repetitions >= 3);
}

void chessClaimDraw50(chess *c)
{
	if (chessCanClaimDraw50(c))
		c->terminal = tsDrawClaimed50MoveRule;
}

void chessClaimDrawThreefold(chess *c)
{
	if (chessCanClaimDrawThreefold(c))
		c->terminal = tsDrawClaimedThreefold;
}

void chessCalculateFields(chess *c)
{
	board *currentBoard = chessGetBoard(c);

	c->repetitions = 0;
	for (boardListNode *n = c->boardHistory->head; n; n = n->next)
	{
		if (boardEqContext(currentBoard, n->board))
			c->repetitions++;
	}

	if (c->currentLegalMoves)
		moveListFree(c->currentLegalMoves);

	c->currentLegalMoves = boardGenerateMoves(currentBoard);

	if (c->currentLegalMoves->size == 0)
	{
		if (boardIsInCheck(currentBoard))
			c->terminal = tsCheckmate;
		else
			c->terminal = tsDrawStalemate;
	}
	else
	{
		if (c->repetitions >= 5)
			c->terminal = tsDrawFivefold;
		else if (currentBoard->halfMoveClock >= 150)
			c->terminal = tsDraw75MoveRule;
		else if (boardIsInsufficientMaterial(currentBoard))
			c->terminal = tsDrawInsufficient;
		else if ((c->terminal != tsDrawClaimed50MoveRule) && (c->terminal != tsDrawClaimedThreefold))
			c->terminal = tsOngoing;
	}
}
