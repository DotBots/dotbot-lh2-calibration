/**
 * @file
 * @date 2022
 * @author Alexandre Abadie <alexandre.abadie@inria.fr>
 * @copyright Inria, 2022
 *
 */

#include <nrf.h>
#include "board.h"
#include "board_config.h"
#include "lh2.h"

static db_lh2_t _lh2;

int main(void) {
    // Initialize the board core features (voltage regulator)
    db_board_init();

    // Initialize the LH2
    db_lh2_init(&_lh2, &db_lh2_d, &db_lh2_e);
    db_lh2_start();

    while (1) {
        __WFE();

        // the location function has to be running all the time
        db_lh2_process_location(&_lh2);
    }
}
