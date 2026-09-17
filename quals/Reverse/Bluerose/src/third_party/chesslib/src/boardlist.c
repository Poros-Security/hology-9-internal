/*
 * Board list implementation
 * Created by thearst3rd on 10/24/2020
 */

#include <stdlib.h>

#include "chesslib/boardlist.h"

boardList *boardListCreate()
{
	boardList *list = (boardList *) malloc(sizeof(boardList));

	list->head = NULL;
	list->tail = NULL;
	list->size = 0;

	return list;
}

boardListNode *boardListNodeCreate(board *b)
{
	boardListNode *node = (boardListNode *) malloc(sizeof(boardListNode));
	node->board = b;
	node->next = NULL;

	return node;
}

void boardListAdd(boardList *list, board *b)
{
	boardListNode *node = boardListNodeCreate(b);

	if (list->head == NULL)
	{
		list->head = node;
		list->tail = node;
	}
	else
	{
		boardListNode *prevTail = list->tail;
		prevTail->next = node;
		list->tail = node;
	}
	list->size++;
}

board *boardListGet(boardList *list, unsigned int index)
{
	boardListNode *currNode = list->head;
	while (index)
	{
		currNode = currNode->next;
		index--;
	}
	return currNode->board;
}

void boardListUndo(boardList *list)
{
	// This would be easier if I made this a doubly linked...
	if (list == NULL || list->head == NULL)
		return;

	if (list->head->next == NULL)
	{
		free(list->head->board);
		free(list->head);
		list->head = NULL;
		list->tail = NULL;
	}
	else
	{
		boardListNode *prev = list->head;
		boardListNode *curr = prev->next;

		while (curr->next)
		{
			prev = curr;
			curr = curr->next;
		}

		free(curr->board);
		free(curr);
		prev->next = NULL;
		list->tail = prev;
	}

	list->size--;
}

void boardListFree(boardList *list)
{
	boardListNode *node = list->head;
	while (node)
	{
		boardListNode *next = node->next;
		free(node->board);
		free(node);
		node = next;
	}
	free(list);
}
