struct Candidate {
	int num;
	int row;
	int col;
};

struct DLX {
	DLX *left;
	DLX *right;
	DLX *up;
	DLX *down;
	DLX *col;

	int size;
	Candidate cand;
};

void cover(DLX *col)
{
	col->right->left = col->left;
	col->left->right = col->right;

	DLX *row = col->down;
	while (row != col) {
		DLX *node = row->right;
		while (node != row) {
			node->down->up = node->up;
			node->up->down = node->down;
			node->col->size--;
			node = node->right;
		}
		row = row->down;
	}
}

void uncover(DLX *col)
{
	DLX *row = col->up;
	while (row != col) {
		DLX *node = row->left;
		while (node != row) {
			node->col->size++;
			node->down->up = node;
			node->up->down = node;
			node = node->left;
		}
		row = row->up;
	}

	col->right->left = col;
	col->left->right = col;
}

void search(DLX *head, int depth)
{
	if (head->right == head) {
		// found a solution
		// TODO: add a callback for the solution
		return;
	}

	DLX *col = head->right;
	DLX *min = col;
	while (col != head) {
		if (col->size < min->size)
			min = col;
		col = col->right;
	}

	cover(min);

	DLX *row = min->down;
	while (row != min) {
		DLX *node = row->right;
		while (node != row) {
			cover(node->col);
			node = node->right;
		}

		search(head, depth + 1);

		node = row->left;
		while (node != row) {
			uncover(node->col);
			node = node->left;
		}

		row = row->down;
	}

	uncover(min);
}
