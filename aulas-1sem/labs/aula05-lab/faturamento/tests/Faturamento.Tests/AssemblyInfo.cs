using Xunit;

// O Singleton do numerador é estado global compartilhado: se duas classes de
// teste rodarem em paralelo, uma enxerga o contador que a outra mexeu e a
// leitura do resultado deixa de significar alguma coisa. Desligar o paralelismo
// entre classes mantém a medição do TODO-6 honesta.
[assembly: CollectionBehavior(DisableTestParallelization = true)]
