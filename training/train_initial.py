from training.ml_pipeline import ml_pipeline

if __name__ == "__main__":
    print("🎯 Entrenamiento inicial de modelos...")
    ml_pipeline.train_all_models(retrain_from_scratch=True)
    print("✅ Modelos entrenados y guardados")