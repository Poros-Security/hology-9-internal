/*
 * Board list definitions
 * Created by thearst3rd on 10/24/2020
 */

#pragma once

#include <stddef.h>

#include "chesslib/board.h"

typedef struct _boardListNode
{
	board *board;
	struct _boardListNode *next;
} boardListNode;

typedef struct
{
	boardListNode *head;
	boardListNode *tail;
	size_t size;
} boardList;

// Creates an empty boardList/boardListNode with given board
boardList *boardListCreate();
boardListNode *boardListNodeCreate(board *b);

// Board list operations
void boardListAdd(boardList *list, board *b);
board *boardListGet(boardList *list, unsigned int index);
void boardListUndo(boardList *list);

// Frees the boardList and all nodes
void boardListFree(boardList *list);
