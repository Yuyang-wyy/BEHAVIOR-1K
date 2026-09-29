# BEHAVIOR-1K 2026: the 100 tasks

One page per task for the high-level planner that prompts the Comet checkpoint. Read `README.md` for how Q is scored and how to prompt Comet.

| # | task | scene | literals | max partial Q | limit (s) | demo skills | ft40k Q | zs Q | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | [turning_on_radio](tasks/00_turning_on_radio.md) | house_double_floor_lower | 1 | 1.0 | 107.5 | 4.0 | 0.0 | 0.0 | yes |
| 1 | [picking_up_trash](tasks/01_picking_up_trash.md) | house_double_floor_lower | 3 | 1.0 | 263.4 | 12.0 | 0.0 | 1.0 | yes |
| 2 | [putting_away_Halloween_decorations](tasks/02_putting_away_Halloween_decorations.md) | house_double_floor_lower | 7 | 0.857 | 689.4 | 27.0 | 0.29 | 0.57 | yes |
| 3 | [cleaning_up_plates_and_food](tasks/03_cleaning_up_plates_and_food.md) | house_double_floor_lower | 7 | 0.571* | 684.8 | 19.0 | 0.0 | 0.0 | yes |
| 4 | [can_meat](tasks/04_can_meat.md) | house_single_floor | 9 | 0.444 | 592.4 | 27.0 | 0.0 | 0.0 | yes |
| 5 | [setting_mousetraps](tasks/05_setting_mousetraps.md) | house_double_floor_upper | 6 | 1.0 | 509.8 | 12.0 | 0.33 | 0.0 | yes |
| 6 | [hiding_Easter_eggs](tasks/06_hiding_Easter_eggs.md) | house_double_floor_lower | 9 | 1.0 | 381.0 | 12.0 | 0.0 | 1.0 | yes |
| 7 | [picking_up_toys](tasks/07_picking_up_toys.md) | house_single_floor | 6 | 1.0 | 944.5 | 26.0 | 0.0 | 0.83 | yes |
| 8 | [rearranging_kitchen_furniture](tasks/08_rearranging_kitchen_furniture.md) | house_double_floor_lower | 4 | 0.75 | 447.2 | 17.0 | 0.5 | 0.0 | yes |
| 9 | [putting_up_Christmas_decorations_inside](tasks/09_putting_up_Christmas_decorations_inside.md) | house_single_floor | 9 | 1.0 | 685.9 | 32.0 | 0.22 | 0.33 | yes |
| 10 | [set_up_a_coffee_station_in_your_kitchen](tasks/10_set_up_a_coffee_station_in_your_kitchen.md) | house_single_floor | 6 | 0.833 | 313.3 | 18.0 | 0.0 | 0.0 | yes |
| 11 | [putting_dishes_away_after_cleaning](tasks/11_putting_dishes_away_after_cleaning.md) | house_single_floor | 14 | 0.571 | 547.7 | 32.0 | 0.5 | 0.0 | yes |
| 12 | [preparing_lunch_box](tasks/12_preparing_lunch_box.md) | house_single_floor | 6 | 0.833 | 412.3 | 23.0 | 0.5 | 0.67 | yes |
| 13 | [loading_the_car](tasks/13_loading_the_car.md) | house_double_floor_lower | 3 | 1.0 | 961.3 | 16.0 | 0.0 | 0.0 | yes |
| 14 | [carrying_in_groceries](tasks/14_carrying_in_groceries.md) | house_double_floor_lower | 4 | 0.75 | 713.7 | 21.0 | 0.0 | 0.25 | yes |
| 15 | [bringing_in_wood](tasks/15_bringing_in_wood.md) | house_double_floor_lower | 3 | 1.0 | 676.8 | 13.0 | 0.0 | 0.0 | yes |
| 16 | [moving_boxes_to_storage](tasks/16_moving_boxes_to_storage.md) | house_double_floor_lower | 2 | 1.0 | 729.8 | 10.0 | 1.0 | 0.5 | yes |
| 17 | [bringing_water](tasks/17_bringing_water.md) | house_single_floor | 3 | 0.667 | 471.9 | 10.0 | 0.0 | 0.0 | yes |
| 18 | [tidying_bedroom](tasks/18_tidying_bedroom.md) | house_single_floor | 3 | 1.0 | 551.9 | 12.0 | 0.67 | 0.67 | yes |
| 19 | [outfit_a_basic_toolbox](tasks/19_outfit_a_basic_toolbox.md) | house_single_floor | 7 | 0.714 | 531.9 | 21.5 | 0.0 | 0.0 | yes |
| 20 | [sorting_vegetables](tasks/20_sorting_vegetables.md) | house_single_floor | 13 | 1.0 | 595.2 | 41.0 | 0.23 | 0.31 | yes |
| 21 | [collecting_childrens_toys](tasks/21_collecting_childrens_toys.md) | house_single_floor | 7 | 1.0 | 959.3 | 28.0 | 0.57 | 0.29 | yes |
| 22 | [putting_shoes_on_rack](tasks/22_putting_shoes_on_rack.md) | house_double_floor_lower | 10 | 1.0 | 386.3 | 14.0 | 0.3 | 0.5 | yes |
| 23 | [boxing_books_up_for_storage](tasks/23_boxing_books_up_for_storage.md) | house_double_floor_upper | 6 | 1.0 | 1211.4 | 31.0 | 0.0 | 0.0 | yes |
| 24 | [storing_food](tasks/24_storing_food.md) | house_single_floor | 8 | 1.0 | 993.5 | 37.5 |  |  | yes |
| 25 | [clearing_food_from_table_into_fridge](tasks/25_clearing_food_from_table_into_fridge.md) | house_double_floor_lower | 5 | 0.8 | 653.4 | 25.0 | 0.2 | 0.4 | yes |
| 26 | [assembling_gift_baskets](tasks/26_assembling_gift_baskets.md) | house_double_floor_lower | 16 | 1.0 | 1303.0 | 68.0 | 0.5 | 0.44 | yes |
| 27 | [sorting_household_items](tasks/27_sorting_household_items.md) | house_single_floor | 8 | 0.875 | 790.4 | 24.0 | 0.0 | 0.5 | yes |
| 28 | [getting_organized_for_work](tasks/28_getting_organized_for_work.md) | house_double_floor_upper | 10 | 0.7 | 783.6 | 43.0 | 0.0 | 0.0 | yes |
| 29 | [clean_up_your_desk](tasks/29_clean_up_your_desk.md) | house_single_floor | 11 | 0.909 | 1070.9 | 42.0 | 0.27 | 0.09 | yes |
| 30 | [setting_the_fire](tasks/30_setting_the_fire.md) | house_double_floor_lower | 8 | 0.875 | 455.9 | 17.0 | 0.75 | 0.12 | yes |
| 31 | [clean_boxing_gloves](tasks/31_clean_boxing_gloves.md) | house_single_floor | 2 | 1.0 | 411.8 | 11.0 | 0.0 | 0.0 | yes |
| 32 | [wash_a_baseball_cap](tasks/32_wash_a_baseball_cap.md) | house_single_floor | 2 | 1.0 | 417.5 | 12.0 | 0.0 | 0.0 | yes |
| 33 | [wash_dog_toys](tasks/33_wash_dog_toys.md) | house_single_floor | 6 | 0.667 | 561.1 | 20.0 | 0.0 | 0.0 | yes |
| 34 | [hanging_pictures](tasks/34_hanging_pictures.md) | house_double_floor_lower | 1 | 1.0 | 119.4 | 5.0 | 0.0 | 0.0 | yes |
| 35 | [attach_a_camera_to_a_tripod](tasks/35_attach_a_camera_to_a_tripod.md) | house_double_floor_upper | 1 | 1.0 | 195.6 | 6.0 | 0.0 | 0.0 | yes |
| 36 | [clean_a_patio](tasks/36_clean_a_patio.md) | house_double_floor_lower | 1 | 1.0 | 603.5 | 51.0 | 0.0 | 0.0 | yes |
| 37 | [clean_a_trumpet](tasks/37_clean_a_trumpet.md) | house_double_floor_upper | 1 | 1.0 | 265.4 | 6.0 | 0.0 | 0.0 | yes |
| 38 | [spraying_for_bugs](tasks/38_spraying_for_bugs.md) | house_double_floor_lower | 2 | 1.0 | 324.0 | 10.0 | 0.0 | 0.5 | yes |
| 39 | [spraying_fruit_trees](tasks/39_spraying_fruit_trees.md) | house_double_floor_lower | 2 | 1.0 | 417.3 | 10.0 | 0.0 | 0.0 | yes |
| 40 | [make_microwave_popcorn](tasks/40_make_microwave_popcorn.md) | house_double_floor_lower | 2 | 1.0 | 161.9 | 8.0 | 0.0 | 0.0 | yes |
| 41 | [cook_cabbage](tasks/41_cook_cabbage.md) | house_single_floor | 4 | 1.0 | 707.2 | 36.0 | 0.0 |  | yes |
| 42 | [chop_an_onion](tasks/42_chop_an_onion.md) | house_double_floor_lower | 4 | 1.0 | 320.0 | 19.5 | 0.5 |  | yes |
| 43 | [slicing_vegetables](tasks/43_slicing_vegetables.md) | house_single_floor | 9 | 0.889 | 742.2 | 37.0 | 0.44 |  | yes |
| 44 | [chopping_wood](tasks/44_chopping_wood.md) | house_double_floor_lower | 8 | 1.0 | 537.6 | 28.0 | 0.0 |  | yes |
| 45 | [cook_hot_dogs](tasks/45_cook_hot_dogs.md) | house_single_floor | 2 | 1.0 | 457.2 | 13.0 | 0.5 |  | yes |
| 46 | [cook_bacon](tasks/46_cook_bacon.md) | house_single_floor | 7 | 0.857 | 384.0 | 14.0 | 0.0 |  | yes |
| 47 | [freeze_pies](tasks/47_freeze_pies.md) | house_single_floor | 7 | 0.857 | 622.8 | 27.0 | 0.0 |  | yes |
| 48 | [canning_food](tasks/48_canning_food.md) | house_single_floor | 10 | 0.4 | 1148.8 | 67.5 | 0.0 |  | yes |
| 49 | [make_pizza](tasks/49_make_pizza.md) | house_double_floor_lower | 2 | 1.0 | 959.3 | 64.0 | 0.0 |  | yes |
| 50 | [freeze_fruit](tasks/50_freeze_fruit.md) | house_single_floor | 7 | 0.857 | 630.9 | 34.0 | 0.0 |  | yes |
| 51 | [cook_a_brisket](tasks/51_cook_a_brisket.md) | house_double_floor_lower | 3 | 0.667 | 366.7 | 17.0 | 0.0 |  | yes |
| 52 | [sorting_bottles_cans_and_paper](tasks/52_sorting_bottles_cans_and_paper.md) | house_double_floor_lower | 16 | 0.375 | 513.2 | 24.0 | 0.06 |  | yes |
| 53 | [tidying_living_room](tasks/53_tidying_living_room.md) | house_double_floor_upper | 4 | 1.0 | 628.3 | 17.0 | 0.5 |  | yes |
| 54 | [putting_away_toys](tasks/54_putting_away_toys.md) | house_single_floor | 8 | 1.0 | 564.8 | 28.0 | 0.75 |  | yes |
| 55 | [re_shelving_library_books](tasks/55_re_shelving_library_books.md) | house_double_floor_upper | 3 | 1.0 | 476.4 | 21.0 | 0.0 |  | yes |
| 56 | [make_rose_centerpieces](tasks/56_make_rose_centerpieces.md) | house_double_floor_lower | 4 | 1.0 | 226.6 | 14.0 | 0.75 | 0.0 | yes |
| 57 | [sweeping_garage](tasks/57_sweeping_garage.md) | house_double_floor_lower | 2 | 1.0 | 223.7 | 4.0 | 0.0 |  | yes |
| 58 | [stacking_wood](tasks/58_stacking_wood.md) | house_single_floor | 6 | 1.0 | 797.0 | 21.0 | 0.0 |  | yes |
| 59 | [organizing_art_supplies](tasks/59_organizing_art_supplies.md) | house_double_floor_upper | 5 | 1.0 | 309.7 | 17.0 | 0.0 |  | yes |
| 60 | [scrubbing_bathroom_floor](tasks/60_scrubbing_bathroom_floor.md) | house_single_floor | 1 | 1.0 | 157.7 | 9.0 | 0.0 | 0.0 | yes |
| 61 | [bringing_paper_to_recycling](tasks/61_bringing_paper_to_recycling.md) | house_double_floor_lower | 3 | 0.667 | 560.7 | 22.0 | 0.0 |  | yes |
| 62 | [halve_an_egg](tasks/62_halve_an_egg.md) | house_single_floor | 5 | 1.0 | 318.9 | 16.0 | 0.0 |  | yes |
| 63 | [installing_smoke_detectors](tasks/63_installing_smoke_detectors.md) | house_double_floor_lower | 1 | 1.0 | 128.4 | 4.0 | 0.0 |  | yes |
| 64 | [setting_the_table](tasks/64_setting_the_table.md) | house_single_floor | 8 | 1.0 | 890.4 | 34.0 |  |  | yes |
| 65 | [unloading_the_car](tasks/65_unloading_the_car.md) | house_double_floor_lower | 2 | 1.0 | 566.2 | 15.0 | 0.0 |  | yes |
| 66 | [turning_out_all_lights_before_sleep](tasks/66_turning_out_all_lights_before_sleep.md) | house_single_floor | 5 | 1.0 | 500.3 | 14.0 | 0.4 |  | yes |
| 67 | [boxing_food_after_dinner](tasks/67_boxing_food_after_dinner.md) | house_single_floor | 6 | 0.833 | 334.9 | 22.0 | 0.5 |  | yes |
| 68 | [cleaning_up_branches_and_twigs](tasks/68_cleaning_up_branches_and_twigs.md) | house_double_floor_lower | 5 | 0.8 | 626.4 | 18.0 | 0.0 |  | yes |
| 69 | [vacuuming_floors](tasks/69_vacuuming_floors.md) | house_double_floor_upper | 1 | 1.0 | 120.6 | 10.0 | 0.0 | 0.0 | yes |
| 70 | [thawing_frozen_food](tasks/70_thawing_frozen_food.md) | house_double_floor_lower | 9 | 0.778 | 411.5 | 15.0 | 0.33 |  | yes |
| 71 | [clean_your_rusty_garden_tools](tasks/71_clean_your_rusty_garden_tools.md) | house_single_floor | 5 | 0.8 | 757.9 | 15.0 | 0.0 |  | yes |
| 72 | [cook_a_frozen_pie](tasks/72_cook_a_frozen_pie.md) | restaurant_diner | 2 | 1.0 | 433.4 | 13.0 | 0.0 |  | yes |
| 73 | [organizing_school_stuff](tasks/73_organizing_school_stuff.md) | house_single_floor | 6 | 1.0 | 729.6 | 25.0 | 0.0 |  | yes |
| 74 | [carrying_out_garden_furniture](tasks/74_carrying_out_garden_furniture.md) | house_single_floor | 2 | 1.0 | 552.9 | 11.0 | 0.0 |  | yes |
| 75 | [put_together_a_basic_pruning_kit](tasks/75_put_together_a_basic_pruning_kit.md) | house_double_floor_lower | 4 | 0.5 | 563.2 | 12.0 | 0.0 |  | yes |
| 76 | [dispose_of_glass](tasks/76_dispose_of_glass.md) | hotel_suite_large | 4 | 1.0 | 459.8 | 17.0 |  |  | yes |
| 77 | [installing_a_modem](tasks/77_installing_a_modem.md) | Rs_int | 4 | 0.75* | 120.6 | 5.0 | 0.25 | 0.0 | yes |
| 78 | [make_cabinet_doors](tasks/78_make_cabinet_doors.md) | Rs_int | 1 | 1.0 | 172.1 | 6.0 |  |  | yes |
| 79 | [polishing_shoes](tasks/79_polishing_shoes.md) | hotel_suite_large | 6 | 0.833 | 536.9 | 15.0 |  |  | yes |
| 80 | [clean_up_broken_glass](tasks/80_clean_up_broken_glass.md) | restaurant_diner | 3 | 1.0 | 434.6 | 11.0 |  |  | yes |
| 81 | [packing_meal_for_delivery](tasks/81_packing_meal_for_delivery.md) | restaurant_diner | 6 | 1.0 | 443.0 | 20.0 |  |  | yes |
| 82 | [store_batteries](tasks/82_store_batteries.md) | Rs_int | 3 | 1.0 | 385.2 | 20.0 |  |  | yes |
| 83 | [store_honey](tasks/83_store_honey.md) | Rs_int | 1 | 1.0 | 338.3 | 18.0 |  |  | yes |
| 84 | [tidying_bathroom](tasks/84_tidying_bathroom.md) | hotel_suite_large | 4 | 1.0 | 650.2 | 20.0 |  |  | yes |
| 85 | [putting_dirty_dishes_in_sink](tasks/85_putting_dirty_dishes_in_sink.md) | restaurant_diner | 4 | 1.0 | 607.4 | 20.0 |  |  | yes |
| 86 | [make_gift_bags_for_baby_showers](tasks/86_make_gift_bags_for_baby_showers.md) | Rs_int | 6 | 1.0 | 482.5 | 24.0 |  |  | yes |
| 87 | [collecting_aluminum_cans](tasks/87_collecting_aluminum_cans.md) | hotel_suite_large | 6 | 1.0 | 510.1 | 20.0 |  |  | yes |
| 88 | [rearrange_your_room](tasks/88_rearrange_your_room.md) | hotel_suite_large | 3 | 1.0 | 642.7 | 14.0 |  |  | yes |
| 89 | [installing_a_fax_machine](tasks/89_installing_a_fax_machine.md) | office_cubicles_right | 2 | 1.0 | 203.8 | 7.0 | 0.0 |  | yes |
| 90 | [composting_waste](tasks/90_composting_waste.md) | Rs_int | 2 | 1.0 | 181.9 | 12.0 | 0.0 |  | yes |
| 91 | [store_produce](tasks/91_store_produce.md) | restaurant_diner | 4 | 1.0 | 476.1 | 20.0 | 0.0 |  | yes |
| 92 | [installing_a_scanner](tasks/92_installing_a_scanner.md) | office_cubicles_right | 2 | 1.0 | 212.9 | 6.0 | 0.0 |  | yes |
| 93 | [clean_a_keyboard](tasks/93_clean_a_keyboard.md) | office_cubicles_right | 1 | 1.0 | 193.8 | 6.0 | 0.0 |  | yes |
| 94 | [dispose_of_batteries](tasks/94_dispose_of_batteries.md) | office_cubicles_right | 4 | 0.75 | 721.4 | 17.0 | 0.0 |  | yes |
| 95 | [cook_brussels_sprouts](tasks/95_cook_brussels_sprouts.md) | restaurant_diner | 26 | 0.923 | 783.1 | 48.0 | 0.0 |  | yes |
| 96 | [cook_broccolini](tasks/96_cook_broccolini.md) | restaurant_diner | 11 | 1.0 | 230.9 | 9.0 | 0.18 |  | yes |
| 97 | [setup_a_bar_for_a_cocktail_party](tasks/97_setup_a_bar_for_a_cocktail_party.md) | restaurant_diner | 20 | 1.0 | 670.9 | 31.0 | 0.5 |  | yes |
| 98 | [laying_tile_floors](tasks/98_laying_tile_floors.md) | office_cubicles_right | 8 | 1.0 | 717.5 | 18.0 | 0.0 |  | yes |
| 99 | [sorting_books_on_shelf](tasks/99_sorting_books_on_shelf.md) | house_double_floor_upper | 11 | 0.36* | 387.0 | 13.0 | 0.0 |  | yes |

\* corrected by the planner notes; the `:init`-based value misses geometry that is already true at reset.
