# **Training a Transformer Model for Hearts Game**

## **1. Overview**
This guide explains how to train a Transformer-based neural network to predict the next card in a Hearts game using previous tricks and game context. The approach includes:
- Pretraining embeddings for the cards using Word2Vec.
- Training a Transformer with frozen embeddings.
- Fine-tuning the embeddings after initial training.
- Managing large datasets efficiently.

## **2. Pretrained Embeddings**
### **Why Use Pretrained Embeddings?**
- **Reduces training time**: The model doesn’t need to learn basic relationships between cards.
- **Improves generalization**: Cards appearing in similar contexts get similar vector representations.
- **Stabilizes learning**: Prevents the model from overfitting to specific tricks.

### **How to Generate Pretrained Embeddings**
- **Train a Word2Vec model** using past game sequences.
- **Save the embeddings** and use them in the Transformer model.

## **3. Model Architecture**
| **Component** | **Details** |
|--------------|-------------|
| **Embedding Layer** | Pretrained 128-dimensional embeddings |
| **Transformer Layers** | 6 Encoder Layers |
| **Attention Heads** | 8 |
| **Hidden Size** | 512 |
| **Batch Size** | 512 |
| **Epochs** | 10 |
| **Learning Rate (Fine-tuning)** | 1e-5 |

## **4. Dataset Management**
Since a full dataset may not fit in memory:
- Use a **data generator** (`tf.keras.utils.Sequence`) to load small batches.
- Use **`tf.data`** for efficient on-the-fly loading.
- Train in **sequential 100K-game chunks**, saving and reloading the model.

## **5. Training Process**
### **Step 1: Train Transformer with Frozen Pretrained Embeddings**
- Load **precomputed embeddings** into the model.
- Train the Transformer while keeping **embeddings frozen**.

### **Step 2: Fine-Tune Embeddings**
- Unfreeze the embedding layer after initial training.
- Lower the learning rate to **1e-5** for fine-tuning.
- Continue training for a few more epochs.

## **6. Performance Optimization on Mac M3 Pro**
- **Enable GPU acceleration** (`tensorflow-metal`).
- **Use mixed precision (`mixed_float16`)** for faster training.
- **Reduce batch size** if memory issues occur.

## **7. Evaluation Strategy**
- **Use Top-K accuracy** instead of strict accuracy.
- **Run Monte Carlo simulations** to test full-game performance.

## **8. Next Steps**
- Evaluate fine-tuning effectiveness.
- Implement Monte Carlo simulations for full-game testing.
- Optimize hyperparameters based on validation results.

