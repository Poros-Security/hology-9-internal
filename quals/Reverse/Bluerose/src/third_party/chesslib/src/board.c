/*
 * Board implementation
 * Created by thearst3rd on 8/23/2020
 */

#include <stdio.h>
#include <ctype.h>
#include <stdlib.h>
#include <string.h>

#include "chesslib/board.h"
#include "chesslib/piecemoves.h"

board *boardCreate()
{
	return boardCreateFromFen(INITIAL_FEN);
}

board *boardCreateFromFen(const char *fen)
{
	board *b = (board *) malloc(sizeof(board));

	if (boardInitFromFenInPlace(b, fen))
	{
		free(b);
		return NULL;
	}

	return b;
}

void boardInitInPlace(board *b)
{
	boardInitFromFenInPlace(b, INITIAL_FEN);
}

uint8_t boardInitFromFenInPlace(board *b, const char *fen)
{
	sq currSq = sqI(1, 8);

	char c;

	// Read in pieces

	while ((c = *fen))
	{
		if (c == ' ')
		{
			break;
		}
		else if (c >= '1' && c <= '8')
		{
			int num = c - '0';
			if (currSq.file + num > 9)
			{
				fprintf(stderr, "ERROR IN FEN: Spacer put file over the end\n");
				return 1;
			}
			for (int i = 0; i < num; i++)
			{
				boardSetPiece(b, currSq, pEmpty);
				currSq.file++;
			}
		}
		else if (c == '/')
		{
			if (currSq.file != 9)
			{
				fprintf(stderr, "ERROR IN FEN: Found '/' at wrong position in rank\n");
				return 1;
			}
			if (currSq.rank <= 1)
			{
				fprintf(stderr, "ERROR IN FEN: Found '/' after the last rank\n");
				return 1;
			}
			currSq.file = 1;
			currSq.rank--;
		}
		else
		{
			if (currSq.file > 8)
			{
				fprintf(stderr, "ERROR IN FEN: Found character '%c' after the end of a rank\n", c);
				return 1;
			}

			char lc = tolower(c);
			int isBlack = islower(c);

			switch (lc)
			{
				case 'p':
					boardSetPiece(b, currSq, isBlack ? pBPawn : pWPawn);
					break;

				case 'n':
					boardSetPiece(b, currSq, isBlack ? pBKnight : pWKnight);
					break;

				case 'b':
					boardSetPiece(b, currSq, isBlack ? pBBishop : pWBishop);
					break;

				case 'r':
					boardSetPiece(b, currSq, isBlack ? pBRook : pWRook);
					break;

				case 'q':
					boardSetPiece(b, currSq, isBlack ? pBQueen : pWQueen);
					break;

				case 'k':
					boardSetPiece(b, currSq, isBlack ? pBKing : pWKing);
					break;

				default:
					fprintf(stderr, "ERROR IN FEN: Unknown character '%c'\n", c);
					return 1;
			}

			currSq.file++;
		}

		fen++;
	}

	if ((currSq.rank != 1) || (currSq.file != 9))
	{
		fprintf(stderr, "ERROR IN FEN: Ended prematurely\n");
		return 1;
	}

	fen++; 	// Go past the last space

	// Read in whose turn it is

	c = *fen;
	switch (c)
	{
		case 'w':
			b->currentPlayer = pcWhite;
			break;
		case 'b':
			b->currentPlayer = pcBlack;
			break;
		default:
			fprintf(stderr, "ERROR IN FEN: Expected 'w' or 'b', found '%c'\n", c);
			return 1;
	}
	fen++;

	c = *fen;
	if (c != ' ')
	{
		fprintf(stderr, "ERROR IN FEN: Expected ' ' after w/b, found '%c'\n", c);
		return 1;
	}
	fen++;

	// Read in castling state
	// NOTE: technically this can match abnormal sequences, but it will match all correct sequences
	// Ex: 'kqqqQQ--k' will function the same as 'Qkq'. This is fine by me

	b->castleState = 0;

	c = *fen;
	while ((c = *fen))
	{
		if (c == ' ')
			break;

		switch (c)
		{
			case '-':
				// Nothing needs to be done
				break;

			case 'K':
				if (boardGetPiece(b, sqI(5, 1)) == pWKing && boardGetPiece(b, sqI(8, 1)) == pWRook)
					b->castleState |= CASTLE_WK;
				break;

			case 'Q':
				if (boardGetPiece(b, sqI(5, 1)) == pWKing && boardGetPiece(b, sqI(1, 1)) == pWRook)
					b->castleState |= CASTLE_WQ;
				break;

			case 'k':
				if (boardGetPiece(b, sqI(5, 8)) == pBKing && boardGetPiece(b, sqI(8, 8)) == pBRook)
					b->castleState |= CASTLE_BK;
				break;

			case 'q':
				if (boardGetPiece(b, sqI(5, 8)) == pBKing && boardGetPiece(b, sqI(1, 8)) == pBRook)
					b->castleState |= CASTLE_BQ;
				break;

			default:
				fprintf(stderr, "ERROR IN FEN: Expected K/Q/k/q or -, found '%c'\n", c);
				return 1;
		}

		fen++;
	}

	fen++; 	// Go past the last space

	// Read in the en passant target square

	c = *fen;
	if (c == '-')
	{
		b->epTarget = SQ_INVALID;
		fen++;
	}
	else
	{
		char epTargetStr[3] = {fen[0], fen[1], 0};
		sq epTarget = sqS(epTargetStr);
		if (epTarget.file == -1) 	// It's invalid
		{
			fprintf(stderr, "ERROR IN FEN: Invalid EP target square \"%s\"\n", epTargetStr);
			return 1;
		}
		b->epTarget = epTarget;
		fen += 2;
	}

	c = *fen;
	if (c != ' ')
	{
		fprintf(stderr, "ERROR IN FEN: Expected ' ' after EP target square, found '%c'\n", c);
		return 1;
	}
	fen++;

	// Read in half move clock and full move count
	// Note: more error checking should probably be done here

	sscanf(fen, "%u %u", &b->halfMoveClock, &b->moveNumber);

	return 0;
}

void boardSetPiece(board *b, sq s, piece p)
{
	int index = sqGetIndex(s);
	b->pieces[index] = p;
}

piece boardGetPiece(board *b, sq s)
{
	int index = sqGetIndex(s);
	return b->pieces[index];
}

// Generates a list of all legal moves. This list must be freed with freeMoveList
moveList *boardGenerateMoves(board *b)
{
	moveList *list = moveListCreate();

	for (int i = 0; i < 64; i++)
	{
		sq s = sqIndex(i);
		piece p = boardGetPiece(b, s);

		if (pieceGetColor(p) != b->currentPlayer)
			continue;

		pieceType type = pieceGetType(p);
		moveList *currMoves = NULL;

		switch (type)
		{
			case ptPawn:
				currMoves = pmGetPawnMoves(b, s);
				break;

			case ptKnight:
				currMoves = pmGetKnightMoves(b, s);
				break;

			case ptBishop:
				currMoves = pmGetBishopMoves(b, s);
				break;

			case ptRook:
				currMoves = pmGetRookMoves(b, s);
				break;

			case ptQueen:
				currMoves = pmGetQueenMoves(b, s);
				break;

			case ptKing:
				currMoves = pmGetKingMoves(b, s);
				break;

			default:
				// Nothing to do
				break;
		}

		if (currMoves)
		{
			board bCheck;
			for (moveListNode *n = currMoves->head; n; n = n->next)
			{
				memcpy(&bCheck, b, sizeof(board)); 	// Done this way so less malloc+freeing required
				move m = n->move;
				boardPlayMoveInPlace(&bCheck, m);
				if (!boardIsPlayerInCheck(&bCheck, b->currentPlayer))
					moveListAdd(list, m);
			}
			moveListFree(currMoves);
		}
	}

	// Can we castle?
	uint8_t castleOO = b->currentPlayer == pcWhite ? (b->castleState & CASTLE_WK) : (b->castleState & CASTLE_BK);
	uint8_t castleOOO = b->currentPlayer == pcWhite ? (b->castleState & CASTLE_WQ) : (b->castleState & CASTLE_BQ);

	if (castleOO || castleOOO)
	{
		uint8_t castleRank = b->currentPlayer == pcWhite ? 1 : 8;
		pieceColor attacker = b->currentPlayer == pcWhite ? pcBlack : pcWhite;

		piece ourKing = b->currentPlayer == pcWhite ? pWKing : pBKing;
		piece ourRook = b->currentPlayer == pcWhite ? pWRook : pBRook;

		if (castleOO)
		{
			if (boardGetPiece(b, sqI(5, castleRank)) == ourKing
					&& boardGetPiece(b, sqI(8, castleRank)) == ourRook
					&& boardGetPiece(b, sqI(6, castleRank)) == pEmpty
					&& boardGetPiece(b, sqI(7, castleRank)) == pEmpty
					&& !boardIsSquareAttacked(b, sqI(5, castleRank), attacker)
					&& !boardIsSquareAttacked(b, sqI(6, castleRank), attacker)
					&& !boardIsSquareAttacked(b, sqI(7, castleRank), attacker))
				moveListAdd(list, moveSq(sqI(5, castleRank), sqI(7, castleRank)));
		}

		if (castleOOO)
		{
			if (boardGetPiece(b, sqI(5, castleRank)) == ourKing
					&& boardGetPiece(b, sqI(1, castleRank)) == ourRook
					&& boardGetPiece(b, sqI(4, castleRank)) == pEmpty
					&& boardGetPiece(b, sqI(3, castleRank)) == pEmpty
					&& boardGetPiece(b, sqI(2, castleRank)) == pEmpty
					&& !boardIsSquareAttacked(b, sqI(5, castleRank), attacker)
					&& !boardIsSquareAttacked(b, sqI(4, castleRank), attacker)
					&& !boardIsSquareAttacked(b, sqI(3, castleRank), attacker))
				moveListAdd(list, moveSq(sqI(5, castleRank), sqI(3, castleRank)));
		}
	}

	return list;
}

uint8_t boardIsSquareAttacked(board *b, sq s, pieceColor attacker)
{
	for (int i = 0; i < 64; i++)
	{
		sq attackerSq = sqIndex(i);
		piece p = boardGetPiece(b, attackerSq);

		if (pieceGetColor(p) != attacker)
			continue;

		pieceType type = pieceGetType(p);
		moveList *currMoves = NULL;

		uint8_t found = 0;

		switch (type)
		{
			case ptPawn:
				currMoves = pmGetPawnAttacks(b, attackerSq);
				break;

			case ptKnight:
				currMoves = pmGetKnightMoves(b, attackerSq);
				break;

			case ptBishop:
				currMoves = pmGetBishopMoves(b, attackerSq);
				break;

			case ptRook:
				currMoves = pmGetRookMoves(b, attackerSq);
				break;

			case ptQueen:
				currMoves = pmGetQueenMoves(b, attackerSq);
				break;

			case ptKing:
				currMoves = pmGetKingMoves(b, attackerSq);
				break;

			default:
				// Nothing to do
				break;
		}

		if (currMoves)
		{
			for (moveListNode *n = currMoves->head; n; n = n->next)
			{
				if (sqEq(s, n->move.to))
				{
					found = 1;
					break;
				}
			}
			moveListFree(currMoves);
			if (found)
				return 1;
		}
	}
	return 0;
}

uint8_t boardIsInCheck(board *b)
{
	return boardIsPlayerInCheck(b, b->currentPlayer);
}

uint8_t boardIsPlayerInCheck(board *b, pieceColor player)
{
	piece royalPiece = (player == pcWhite) ? pWKing : pBKing;
	pieceColor otherColor = (player == pcWhite) ? pcBlack : pcWhite;
	for (int i = 0; i < 64; i++)
	{
		sq s = sqIndex(i);
		if (boardGetPiece(b, s) == royalPiece)
		{
			if (boardIsSquareAttacked(b, s, otherColor))
				return 1;
		}
	}
	return 0;
}

uint8_t boardIsInsufficientMaterial(board *b)
{
	uint8_t numPieces = 0;
	uint8_t numKnights = 0;
	uint8_t numBishopsDark = 0;
	uint8_t numBishopsLight = 0;
	// For handling multiple/no kings
	uint8_t numWhiteKings = 0;
	uint8_t numBlackKings = 0;

	for (int i = 0; i < 64; i++)
	{
		sq s = sqIndex(i);
		piece p = boardGetPiece(b, s);
		pieceType pt = pieceGetType(p);

		if (pt != ptEmpty)
			numPieces++;

		if (p == pWKing)
			numWhiteKings++;

		if (p == pBKing)
			numBlackKings++;

		if (pt == ptKnight)
			numKnights++;

		if (pt == ptBishop)
		{
			if (sqIsDark(s))
				numBishopsDark++;
			else
				numBishopsLight++;
		}
	}

	// Just kings, always a draw
	if (numPieces == numWhiteKings + numBlackKings)
		return 1;

	// For now, only handle normal case
	if (numWhiteKings == 1 && numBlackKings == 1)
	{
		// Just kings and minor pieces
		if (numPieces == (2 + numKnights + numBishopsDark + numBishopsLight))
		{
			// Kings + 1 minor is draw
			if (numPieces == 3)
				return 1;

			// Kings + only bishops, all on the same color
			if (numKnights == 0 && (numBishopsLight == 0 || numBishopsDark == 0))
				return 1;
		}
	}
	// TODO - write an else here. Or just say that's beyond scope...

	return 0;
}

// Returns a new board on which the given move was played on the given board
// NOTE - this assumes that the move is legal!
board *boardPlayMove(board *b, move m)
{
	board *newBoard = (board *) malloc(sizeof(board));
	memcpy(newBoard, b, sizeof(board));

	boardPlayMoveInPlace(newBoard, m);

	return newBoard;
}

// Plays the given move on the given board, modifying the given board's memory in place
// NOTE - this assumes that the move is legal!
void boardPlayMoveInPlace(board *b, move m)
{
	// Update the counters
	if (b->currentPlayer == pcBlack)
		b->moveNumber++;

	// Was this in irreversable move?
	pieceType pt = pieceGetType(boardGetPiece(b, m.from));
	if (pt == ptPawn || (boardGetPiece(b, m.to) != pEmpty))
		b->halfMoveClock = 0;
	else
		b->halfMoveClock++;

	// Is this a castling move?
	if (pt == ptKing)
	{
		// TODO - maybe redesign this to work better with Chess 960, though I don't like Fischer castling >:(
		int8_t diffFile = m.to.file - m.from.file;
		if (diffFile == 2) 	// O-O
		{
			// Move rook from h file to correct file
			boardSetPiece(b, sqI(8, m.to.rank), pEmpty);
			boardSetPiece(b, sqI(m.to.file - 1, m.to.rank), b->currentPlayer == pcWhite ? pWRook : pBRook);
		}
		else if (diffFile == -2) 	// O-O-O
		{
			// Move rook from a file to correct file
			boardSetPiece(b, sqI(1, m.to.rank), pEmpty);
			boardSetPiece(b, sqI(m.to.file + 1, m.to.rank), b->currentPlayer == pcWhite ? pWRook : pBRook);
		}
		b->castleState &= ~((b->currentPlayer == pcWhite) ? (CASTLE_WK | CASTLE_WQ) : (CASTLE_BK | CASTLE_BQ));
	}
	else if (pt == ptRook)
	{
		// Did a rook just move that should clear a castling flag?
		if (sqEq(m.from, sqI(8, 1)))
			b->castleState &= ~CASTLE_WK;
		if (sqEq(m.from, sqI(1, 1)))
			b->castleState &= ~CASTLE_WQ;
		if (sqEq(m.from, sqI(8, 8)))
			b->castleState &= ~CASTLE_BK;
		if (sqEq(m.from, sqI(1, 8)))
			b->castleState &= ~CASTLE_BQ;
	}

	// Did a rook just get captured that should clear a castling flag?
	if (sqEq(m.to, sqI(8, 1)))
		b->castleState &= ~CASTLE_WK;
	if (sqEq(m.to, sqI(1, 1)))
		b->castleState &= ~CASTLE_WQ;
	if (sqEq(m.to, sqI(8, 8)))
		b->castleState &= ~CASTLE_BK;
	if (sqEq(m.to, sqI(1, 8)))
		b->castleState &= ~CASTLE_BQ;

	// Is this an en passant capture?
	if (pt == ptPawn && sqEq(b->epTarget, m.to))
	{
		// Remove the captured pawn
		uint8_t delta = (b->currentPlayer == pcWhite) ? -1 : 1;
		boardSetPiece(b, sqI(m.to.file, m.to.rank + delta), pEmpty);
	}

	// Move the piece
	boardSetPiece(b,
			m.to,
			(m.promotion == ptEmpty) ? boardGetPiece(b, m.from) : pieceMake(m.promotion, b->currentPlayer));
	boardSetPiece(b, m.from, pEmpty);

	// Should this set the EP target square?
	int8_t diffRank = m.to.rank - m.from.rank;
	if (pt == ptPawn && ((diffRank == 2) || (diffRank == -2)))
	{
		int8_t delta = (b->currentPlayer == pcWhite) ? -1 : 1;
		b->epTarget = sqI(m.to.file, m.to.rank + delta);
	}
	else
	{
		b->epTarget = SQ_INVALID;
	}

	// Switch current player
	b->currentPlayer = (b->currentPlayer == pcWhite) ? pcBlack : pcWhite;
}

// Board equality - returns true if boards are fully equal
uint8_t boardEq(board *b1, board *b2)
{
	if (b1->currentPlayer != b2->currentPlayer)
		return 0;

	if (b1->castleState != b2->castleState)
		return 0;

	if (!sqEq(b1->epTarget, b2->epTarget))
		return 0;

	if (b1->halfMoveClock != b2->halfMoveClock)
		return 0;

	if (b1->moveNumber != b2->moveNumber)
		return 0;

	if (memcmp(b1, b2, 64 * sizeof(piece)))
		return 0;

	return 1;
}

// Contextual board equality - doesn't consider counters, and filters out EP target square
uint8_t boardEqContext(board *b1, board *b2)
{
	if (b1->currentPlayer != b2->currentPlayer)
		return 0;

	if (b1->castleState != b2->castleState)
		return 0;

	if (memcmp(b1, b2, 64 * sizeof(piece)))
		return 0;

	// Filter EP target squares
	sq b1EpTarget = b1->epTarget;
	if (!sqEq(b1EpTarget, SQ_INVALID))
	{
		// Are there actually any pawns that can attack this square? If not, make it SQ_INVALID
		int delta = b1->currentPlayer == pcWhite ? -1 : 1;
		piece p = b1->currentPlayer == pcWhite ? pWPawn : pBPawn;

		int found = 0;

		sq from = sqI(b1EpTarget.file - 1, b1EpTarget.rank + delta);
		if (boardGetPiece(b1, from) == p)
		{
			board b;
			memcpy(&b, b1, sizeof(board));
			boardPlayMoveInPlace(&b, moveSq(from, b1EpTarget));
			if (!boardIsPlayerInCheck(&b, b1->currentPlayer))
				found = 1;
		}

		from = sqI(b1EpTarget.file + 1, b1EpTarget.rank + delta);
		if ((!found) && (boardGetPiece(b1, from) == p))
		{
			board b;
			memcpy(&b, b1, sizeof(board));
			boardPlayMoveInPlace(&b, moveSq(from, b1EpTarget));
			if (!boardIsPlayerInCheck(&b, b1->currentPlayer))
				found = 1;
		}

		if (!found)
			b1EpTarget = SQ_INVALID;
	}

	sq b2EpTarget = b2->epTarget;
	if (!sqEq(b2EpTarget, SQ_INVALID))
	{
		// Are there actually any pawns that can attack this square? If not, make it SQ_INVALID
		int delta = b2->currentPlayer == pcWhite ? -1 : 1;
		piece p = b2->currentPlayer == pcWhite ? pWPawn : pBPawn;

		int found = 0;

		sq from = sqI(b2EpTarget.file - 1, b2EpTarget.rank + delta);
		if (boardGetPiece(b2, from) == p)
		{
			board b;
			memcpy(&b, b2, sizeof(board));
			boardPlayMoveInPlace(&b, moveSq(from, b2EpTarget));
			if (!boardIsPlayerInCheck(&b, b2->currentPlayer))
				found = 1;
		}

		from = sqI(b2EpTarget.file + 1, b2EpTarget.rank + delta);
		if ((!found) && (boardGetPiece(b2, from) == p))
		{
			board b;
			memcpy(&b, b2, sizeof(board));
			boardPlayMoveInPlace(&b, moveSq(from, b2EpTarget));
			if (!boardIsPlayerInCheck(&b, b2->currentPlayer))
				found = 1;
		}

		if (!found)
			b2EpTarget = SQ_INVALID;
	}

	if (!sqEq(b1EpTarget, b2EpTarget))
		return 0;

	return 1;
}

// Returns a FEN string from the given board. Must be freed
char *boardGetFen(board *b)
{
	char buf[104];
	char *c = buf;

	// Pieces
	for (uint8_t rank = 8; rank >= 1; rank--)
	{
		uint8_t blanks = 0;
		for (uint8_t file = 1; file <= 8; file++)
		{
			sq s = sqI(file, rank);
			piece p = boardGetPiece(b, s);
			if (p)
			{
				if (blanks > 0)
				{
					*c++ = '0' + blanks;
					blanks = 0;
				}
				*c++ = pieceGetLetter(p);
			}
			else
			{
				blanks++;
			}
		}

		if (blanks > 0)
		{
			*c++ = '0' + blanks;
		}

		if (rank > 1)
		{
			*c++ = '/';
		}
	}

	*c++ = ' ';

	// Current player
	if (b->currentPlayer == pcWhite)
		*c++ = 'w';
	else
		*c++ = 'b';

	*c++ = ' ';

	// Castling state
	if (b->castleState == 0)
	{
		*c++ = '-';
	}
	else
	{
		if (b->castleState & CASTLE_WK)
			*c++ = 'K';
		if (b->castleState & CASTLE_WQ)
			*c++ = 'Q';
		if (b->castleState & CASTLE_BK)
			*c++ = 'k';
		if (b->castleState & CASTLE_BQ)
			*c++ = 'q';
	}

	*c++ = ' ';

	// EP target
	if (sqEq(b->epTarget, SQ_INVALID))
	{
		*c++ = '-';
	}
	else
	{
		const char *ep = sqGetStr(b->epTarget);
		*c++ = ep[0];
		*c++ = ep[1];
	}

	*c++ = ' ';

	// Fill in the rest of the string with half move clock and move number
	sprintf(c, "%u %u", b->halfMoveClock, b->moveNumber);

	size_t len = strlen(buf);
	char *str = (char *) malloc((len + 1) * sizeof(char));
	strcpy(str, buf);
	return str;
}
