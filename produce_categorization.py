from enum import Enum
import hydra
from omegaconf import DictConfig
from utils.load_from_json import load_prompt_ranking_from_json
from utils.validation import validate_config
from pathlib import Path
from logging import getLogger
from utils.load_from_json import JsonFormat
from hydra.utils import to_absolute_path
import json
get_logger = getLogger
logger = get_logger(__name__)


class QuestionCategory(Enum):
    IS_OPEN_WATER = "is_open_water"
    IS_COASTLINE = "is_coastline"
    IS_USV = "is_usv"
    IS_UAV = "is_uav"
    NO_SHIPS = "no_ships"
    BIRDS_BUOYS = "birds_buoys"
    ONE_TO_FOUR_SHIPS = "one_to_four_ships"
    FIVE_TO_NINE_SHIPS = "five_to_nine_ships"
    TEN_TO_FOURTEEN_SHIPS = "ten_to_fourteen_ships"
    FIFTEEN_PLUS_SHIPS = "fifteen_or_more_ships"

SHIP_COUNT_QUESTION_CATEGORIES = [
    QuestionCategory.ONE_TO_FOUR_SHIPS,
    QuestionCategory.FIVE_TO_NINE_SHIPS,
    QuestionCategory.TEN_TO_FOURTEEN_SHIPS,
    QuestionCategory.FIFTEEN_PLUS_SHIPS,
    QuestionCategory.NO_SHIPS
]


class AndurilQuestionWeights:
    def __init__(self):
        self.is_open_water = "is_open_water"
        self.is_coastline = "is_coastline"
        self.is_usv = "is_usv"
        self.is_uav = "is_uav"

    def get_question_weights(self, question_category: QuestionCategory):
        return {
            self.is_open_water: (
                1.0 if question_category == QuestionCategory.IS_OPEN_WATER else 0.0
            ),
            self.is_coastline: (
                1.0 if question_category == QuestionCategory.IS_COASTLINE else 0.0
            ),
            self.is_usv: 1.0 if question_category == QuestionCategory.IS_USV else 0.0,
            self.is_uav: 1.0 if question_category == QuestionCategory.IS_UAV else 0.0,
            QuestionCategory.BIRDS_BUOYS.value: 1.0 if question_category == QuestionCategory.BIRDS_BUOYS else 0.0,
            QuestionCategory.NO_SHIPS.value: 1.0 if question_category == QuestionCategory.NO_SHIPS else 0.0,
            QuestionCategory.ONE_TO_FOUR_SHIPS.value: 1.0 if question_category == QuestionCategory.ONE_TO_FOUR_SHIPS else 0.0,
            QuestionCategory.FIVE_TO_NINE_SHIPS.value: 1.0 if question_category == QuestionCategory.FIVE_TO_NINE_SHIPS else 0.0,
            QuestionCategory.TEN_TO_FOURTEEN_SHIPS.value: 1.0 if question_category == QuestionCategory.TEN_TO_FOURTEEN_SHIPS else 0.0,
            QuestionCategory.FIFTEEN_PLUS_SHIPS.value: 1.0 if question_category == QuestionCategory.FIFTEEN_PLUS_SHIPS else 0.0,
        }

    def get_type(self, is_type: bool, question_category: QuestionCategory):
        if question_category == QuestionCategory.IS_OPEN_WATER:
            return "open_water_or_coastline", "open_water" if is_type else "coastline"

        elif question_category == QuestionCategory.IS_COASTLINE:
            return "open_water_or_coastline", "coastline" if is_type else "open_water"
        
        elif question_category == QuestionCategory.IS_USV:
            return "uav_or_usv", "usv" if is_type else "uav"

        elif question_category == QuestionCategory.IS_UAV:
            return "uav_or_usv", "uav" if is_type else "usv"

        else:
            raise ValueError(f"Invalid question category: {question_category}")


def extract_ship_count_type(json_scores_file, image_dir, json_format, anduril_question_weights, birds_buoys_threshold: float) -> dict[str, str]:
    results: dict[str, list[tuple[QuestionCategory, float]]] = {
    }

    for question_category in SHIP_COUNT_QUESTION_CATEGORIES:
        question_weights = anduril_question_weights.get_question_weights(question_category)
        ranked_results = load_prompt_ranking_from_json(
            json_scores_file, image_dir, question_weights, json_format
        )
        assert len(ranked_results) == 1
        final_scores = ranked_results[0].final_scores
        for image_score in final_scores:
            img_name = image_score.img_name
            if img_name not in results.keys():
                results[img_name] = []
            results[img_name].append((question_category, image_score.similarity))
    
    question_weights = anduril_question_weights.get_question_weights(QuestionCategory.BIRDS_BUOYS)
    ranked_results = load_prompt_ranking_from_json(
        json_scores_file, image_dir, question_weights, json_format
    )
    assert len(ranked_results) == 1
    final_scores = ranked_results[0].final_scores

    results_birds_buoys = {
        image_score.img_name: image_score.similarity for image_score in final_scores
    }
    
    results_final = {}
    for img_name, scores in results.items():
        scores.sort(key=lambda x: x[1], reverse=True)
        highest_score_category = scores[0][0]

        if highest_score_category == QuestionCategory.NO_SHIPS:
            if results_birds_buoys[img_name] > birds_buoys_threshold:
                results_final[img_name] = QuestionCategory.BIRDS_BUOYS.value
            else:
                results_final[img_name] = QuestionCategory.NO_SHIPS.value
        else:
            results_final[img_name] = highest_score_category.value

    return results_final


@hydra.main(config_path="config", config_name="config", version_base=None)
def main(cfg: DictConfig) -> None:
    """Load metadata, score images for each prompt, and write a Markdown report."""
    logger.info(f"Starting similarity ranking with config: {cfg}")

    validate_config(cfg)

    # CONFIG >>>>>>>>>>>>
    json_scores_file = Path(to_absolute_path(cfg.json_scores_file))
    image_dir = Path(to_absolute_path(cfg.image_dir))
    json_format: JsonFormat = JsonFormat(cfg.json_format)
    anduril_question_weights = AndurilQuestionWeights()
    threshholds = {
        QuestionCategory.IS_OPEN_WATER: 0.82,
        QuestionCategory.IS_COASTLINE: 1000000,
        QuestionCategory.IS_USV: 0.3,
        QuestionCategory.IS_UAV: 1000000,
    }
    birds_buoys_threshold = 0.5
    types_to_check = [QuestionCategory.IS_USV, QuestionCategory.IS_OPEN_WATER]
    output_json_fpath = Path("categorization.json")

    # <<<<<<<<<<<<<<<<<<<<

    # GENERATE MARKDOWN >>>
    logger.info(f"Loading prompt rankings from JSON file: {json_scores_file}")
     
    categorized_results = {} # img_name: uav_or_usv, open_water_or_coastline, ship_count_type (birdbouys, nothing, 1-4. 5-9, 10-14, 15+)

    for category in types_to_check:
        question_weights = anduril_question_weights.get_question_weights(category)
        ranked_results = load_prompt_ranking_from_json(
            json_scores_file, image_dir, question_weights, json_format
        )
        threshold = threshholds[category]
        
        assert len(ranked_results) == 1
        ranking = ranked_results[0]

        for image_score in ranking.final_scores:
            img_name = image_score.img_name
            is_type = image_score.similarity > threshold

            #if category == QuestionCategory.IS_OPEN_WATER and image_score.similarity > 0.7:
            #    print(img_name, is_type, image_score.similarity)
            #    print(question_weights)
            type_name, type_value = anduril_question_weights.get_type(is_type, category)
            
            if img_name not in categorized_results.keys():
                categorized_results[img_name] = {}

            categorized_results[img_name][type_name] = type_value
    
    ship_types = extract_ship_count_type(json_scores_file, image_dir, json_format, anduril_question_weights, birds_buoys_threshold)
    for img_name, ship_type in ship_types.items():
        categorized_results[img_name]["ship_type"] = ship_type

    with open(output_json_fpath, "w") as f:
        f.write(json.dumps(categorized_results, indent=4))
    # <<<<<<<<<<<<<<<<<<<<<

if __name__ == "__main__":
    main()
